"""Реальный пайплайн: baseline из COAST_WAYPOINTS -> трансекты -> для каждого
года сэмплируем MNDWI вдоль трансект -> позиция берега = точка перехода
суша/вода по порогу Оцу -> регрессия по годам -> риск/прогноз для объектов.

Направление трансект проверяется эмпирически на одном опорном году: обе
стороны нормали пробуются, побеждает та, что реально даёт переход
суша->вода на большинстве трансект (грабля #1 из прошлого прогона —
здесь она ловится по настоящим пикселям, а не по геометрии-заглушке).

Координаты 8 объектов инфраструктуры пока приблизительные (взяты из
pipeline/mock/generate.py) — команде нужно заменить на размеченные в
geojson.io согласно README.md. Расстояния и риск при этом всё равно
считаются по настоящим спутниковым данным через ближайшую трансекту.

Запуск (пример на 3 годах, дальше можно расширить до --years 2000-2026):
    python3 -m pipeline.gee.run_real_pipeline --years 2000,2013,2026 --out data/real
"""
import argparse
import json
import time
from pathlib import Path

import ee
import pyproj
from shapely.geometry import LineString
from shapely.ops import transform

from pipeline.gee import config as cfg
from pipeline.gee.composite import build_year_composite
from pipeline.gee.geometry import coastal_corridor
from pipeline.gee.indices import mndwi
from pipeline.gee.otsu import otsu_threshold
from pipeline.gee.sample_transects import WORK_SCALE_FLOOR_M, find_crossing, sample_mndwi_along_transects
from pipeline.mock.generate import OBJECT_DEFS
from pipeline.risk.engine import compute_risk
from pipeline.forecast.scenarios import build_scenarios
from pipeline.transects.baseline import build_baseline
from pipeline.transects.displacement import build_transect_record
from pipeline.transects.generate import TransectDirectionError, cast_transects

_TO_OUTPUT = pyproj.Transformer.from_crs(cfg.CRS_METRIC, cfg.CRS_OUTPUT, always_xy=True).transform


def _year_mndwi_and_threshold(year: int, aoi: ee.Geometry, corridor: ee.Geometry, work_scale: int = WORK_SCALE_FLOOR_M):
    composite, coll_id, n_scenes, window = build_year_composite(year, aoi)
    if composite is None:
        return None
    index_img = mndwi(composite, coll_id)
    threshold = otsu_threshold(index_img, corridor, scale=work_scale).getInfo()
    return index_img, threshold, coll_id, n_scenes, window, work_scale


def pick_direction(baseline, aoi, corridor, reference_year: int, min_hit_fraction: float = 0.55):
    t0 = time.time()
    ref = _year_mndwi_and_threshold(reference_year, aoi, corridor)
    if ref is None:
        raise RuntimeError(f"Нет снимков для опорного года {reference_year} — нечем проверить направление трансект")
    index_img, threshold, coll_id, n_scenes, window, scale = ref
    print(f"  [{time.time()-t0:.1f}s] composite+otsu готовы, threshold={threshold:.4f}")

    scores, candidates = {}, {}
    for sign in (1, -1):
        transects = cast_transects(baseline, sign)
        t1 = time.time()
        samples = sample_mndwi_along_transects(index_img, transects, scale)
        hits = sum(1 for t_id in samples if find_crossing(samples[t_id], threshold) is not None)
        scores[sign] = hits / len(transects)
        candidates[sign] = transects
        print(f"  [{time.time()-t0:.1f}s] sign={sign}: {scores[sign]:.0%} трансект дали пересечение "
              f"({time.time()-t1:.1f}s на сэмплинг {len(transects)} трансект)")

    best_sign = max(scores, key=scores.get)
    print(f"  направление нормали: +1={scores[1]:.0%}, -1={scores[-1]:.0%} -> выбрано {best_sign}")
    if scores[best_sign] < min_hit_fraction:
        raise TransectDirectionError(
            f"Ни одно направление трансект не даёт устойчивого перехода суша/вода "
            f"(лучшее {scores[best_sign]:.0%} на годе {reference_year}). "
            f"Проверьте COAST_WAYPOINTS в pipeline/gee/config.py — похоже, baseline не идёт вдоль берега."
        )
    return best_sign, candidates[best_sign]


def run(years: list[int], out_dir: Path, project: str, reference_year: int):
    ee.Initialize(project=project)
    aoi = ee.Geometry.Rectangle([
        cfg.AOI_MANGYSTAU["coordinates"][0][0][0], cfg.AOI_MANGYSTAU["coordinates"][0][0][1],
        cfg.AOI_MANGYSTAU["coordinates"][0][2][0], cfg.AOI_MANGYSTAU["coordinates"][0][2][1],
    ])
    corridor = coastal_corridor()

    baseline = build_baseline()
    print(f"Baseline: {round(baseline.length / 1000, 1)} км, проверяю направление трансект на {reference_year}...")
    sign, transects = pick_direction(baseline, aoi, corridor, reference_year)
    print(f"Трансект построено: {len(transects)}")

    positions_by_transect: dict[int, dict[int, float | None]] = {i: {} for i in range(len(transects))}
    shorelines_out_dir = out_dir / "shorelines"
    shorelines_out_dir.mkdir(parents=True, exist_ok=True)

    for year in years:
        t0 = time.time()
        print(f"{year}: сэмплирование...")
        result = _year_mndwi_and_threshold(year, aoi, corridor)
        if result is None:
            print(f"  {year}: нет снимков — все трансекты null")
            for i in range(len(transects)):
                positions_by_transect[i][year] = None
            continue
        index_img, threshold, coll_id, n_scenes, window, scale = result
        samples = sample_mndwi_along_transects(index_img, transects, scale)

        crossing_points_wgs84 = []
        for i, t in enumerate(transects):
            # find_crossing даёт расстояние от суши (начало трансекты) до воды —
            # это растёт, когда море отступает. Конвенция всего проекта обратная
            # (отрицательная скорость = отступление, как "расстояние от опорной
            # точки в море до берега", а не наоборот) — храним со знаком минус,
            # чтобы регрессия и total_retreat_m считались уже в общей конвенции.
            pos = find_crossing(samples.get(i, []), threshold)
            positions_by_transect[i][year] = -pos if pos is not None else None
            if pos is not None:
                pt = t.interpolate(pos)
                crossing_points_wgs84.append(list(transform(_TO_OUTPUT, pt).coords)[0])

        if len(crossing_points_wgs84) >= 2:
            fc = {
                "type": "FeatureCollection",
                "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
                "features": [{
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": crossing_points_wgs84},
                    "properties": {
                        "year": year, "sensor": coll_id, "scale_m": scale, "n_scenes": n_scenes,
                        "date_window": list(window), "otsu_threshold": round(threshold, 4),
                        "data_quality": "good",
                        "length_km": round(LineString(crossing_points_wgs84).length * 96, 1),
                    },
                }],
            }
            (shorelines_out_dir / f"shoreline_{year}.geojson").write_text(
                json.dumps(fc, ensure_ascii=False), encoding="utf-8")
        n_found = sum(1 for i in range(len(transects)) if positions_by_transect[i][year] is not None)
        print(f"  {year}: OK ({time.time()-t0:.1f}s), {n_scenes} сцен, otsu={round(threshold, 4)}, "
              f"позиция найдена для {n_found}/{len(transects)} трансект")

    transect_features = []
    for i, t in enumerate(transects):
        rec = build_transect_record(i + 1, t, positions_by_transect[i], years)
        line_wgs84 = transform(_TO_OUTPUT, rec["geometry_metric"])
        transect_features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": list(line_wgs84.coords)},
            "properties": {
                "transect_id": rec["transect_id"],
                "baseline_distance_m": round(i * cfg.TRANSECT_SPACING_M, 1),
                "positions": {str(y): rec["positions"].get(y) for y in years},
                "total_retreat_m": rec["total_retreat_m"],
                "speed_m_per_year": rec["speed_m_per_year"],
                "r_squared": rec["r_squared"],
                "std_error": rec["std_error"],
                "ci_95_low": rec["ci_95_low"],
                "ci_95_high": rec["ci_95_high"],
                "valid_years": rec["valid_years"],
                "confidence": rec["confidence"],
                "risk_class": rec["risk_class"],
                "anchor": list(line_wgs84.coords)[0],
            },
        })
    transects_fc = {"type": "FeatureCollection", "features": transect_features}
    (out_dir / "transects.geojson").write_text(json.dumps(transects_fc, ensure_ascii=False), encoding="utf-8")
    print(f"\ntransects.geojson: {len(transect_features)} трансект")

    objects_features = _build_objects(transect_features, years)
    (out_dir / "objects.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": objects_features}, ensure_ascii=False), encoding="utf-8")
    print(f"objects.geojson: {len(objects_features)} объектов (координаты приблизительные, см. README.md)")


def _nearest_distance(positions: dict, target_year: int, years: list[int]) -> float:
    """abs(position) на нужный год, либо на ближайший доступный, если данных
    за сам год нет (снимок не найден/облачно)."""
    v = positions.get(str(target_year))
    if v is not None:
        return abs(v)
    candidates = sorted((y for y in years if positions.get(str(y)) is not None),
                         key=lambda y: abs(y - target_year))
    return abs(positions[str(candidates[0])]) if candidates else 0.0


def _build_objects(transect_features, years):
    import math
    features = []
    for od in OBJECT_DEFS:
        best, best_d = None, float("inf")
        for f in transect_features:
            ax, ay = f["properties"]["anchor"]
            d = math.hypot(ax - od["lon"], ay - od["lat"])
            if d < best_d:
                best, best_d = f, d
        if best is None:
            continue
        speed = best["properties"]["speed_m_per_year"]
        positions = best["properties"]["positions"]
        last_year = years[-1]

        d2000 = _nearest_distance(positions, 2000, years)
        d2010 = _nearest_distance(positions, 2010, years)
        d2020 = _nearest_distance(positions, 2020, years)
        d2026 = _nearest_distance(positions, 2026, years)
        d_last = _nearest_distance(positions, last_year, years)

        risk = compute_risk(speed, d2026, od["category"])
        forecast = build_scenarios(d2026, speed, last_year)
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [od["lon"], od["lat"]]},
            "properties": {
                "object_id": od["object_id"],
                "name_ru": od["name_ru"], "name_kk": od["name_kk"], "name_en": od["name_en"],
                "category": od["category"], "criticality": risk["criticality"],
                "nearest_transect_id": best["properties"]["transect_id"],
                "distance_to_shore_2000_m": round(d2000, 1),
                "distance_to_shore_2010_m": round(d2010, 1),
                "distance_to_shore_2020_m": round(d2020, 1),
                "distance_to_shore_2026_m": round(d2026, 1),
                "speed_m_per_year": speed,
                "risk_score": risk["score"], "risk_level": risk["level"],
                "risk_components": risk["components"],
                "forecast": forecast,
                "description_ru": od["description_ru"], "description_kk": od["description_kk"], "description_en": od["description_en"],
                "recommendation_ru": od["recommendation_ru"], "recommendation_en": od["recommendation_en"],
                "source": "реальные спутниковые данные; координаты объекта — временные, см. README.md",
            },
        })
    return features


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", default="2000,2013,2026")
    parser.add_argument("--out", default="data/real")
    parser.add_argument("--project", default="caspian-pulse-ee")
    parser.add_argument("--reference-year", type=int, default=2026)
    args = parser.parse_args()

    spec = args.years
    years = set()
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            years.update(range(int(a), int(b) + 1))
        else:
            years.add(int(part))
    years = sorted(years - set(cfg.MISSING_YEARS))

    out_dir = Path(__file__).resolve().parents[2] / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    run(years, out_dir, args.project, args.reference_year)


if __name__ == "__main__":
    main()
