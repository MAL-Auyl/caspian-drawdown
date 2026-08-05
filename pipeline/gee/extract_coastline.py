"""Извлечение береговой линии Каспия по годам: MNDWI + порог Оцу → маска
воды → векторизация → урез воды как LineString.

Запуск:
    python3 -m pipeline.gee.extract_coastline --years 2000,2013,2026
    python3 -m pipeline.gee.extract_coastline --years 2000-2026 --out pipeline/data/real/shorelines

Полигон водной маски после reduceToVectors может касаться границы AOI —
это ожидаемо (AOI сильно шире прибрежной полосы, которую реально сэмплируют
трансекты) и не мешает шагу трансект: там берётся ближайшее к суше
пересечение луча с линией, а не любое пересечение.
"""
import argparse
import json
from pathlib import Path

import ee

from pipeline.gee import config as cfg
from pipeline.gee.composite import build_year_composite
from pipeline.gee.geometry import coastal_corridor
from pipeline.gee.indices import mndwi
from pipeline.gee.otsu import otsu_threshold


def parse_years(spec: str) -> list[int]:
    years = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            years.update(range(int(a), int(b) + 1))
        else:
            years.add(int(part))
    return sorted(y for y in years if y not in cfg.MISSING_YEARS)


def largest_water_ring(water_mask: ee.Image, aoi: ee.Geometry, scale: int):
    """Векторизует крупнейший водный полигон в aoi и возвращает его контур
    как LineString — но контур полигона, обрезанного по aoi, неизбежно
    включает и кусок самой границы aoi (там, где вода касается края области
    векторизации), а не только настоящий урез воды. Отсекаем это: пересекаем
    контур с чуть уменьшенным aoi, оставляя только внутренние (настоящие)
    участки границы, и берём самый длинный кусок."""
    vectors = water_mask.selfMask().reduceToVectors(
        geometry=aoi, scale=scale, geometryType="polygon",
        maxPixels=1e10, bestEffort=True, tileScale=4, eightConnected=True,
    )
    with_area = vectors.map(lambda f: f.set("area_m2", f.geometry().area(1)))
    largest = ee.Feature(with_area.sort("area_m2", False).first())
    ring = ee.Geometry.LineString(largest.geometry().simplify(cfg.SIMPLIFY_TOLERANCE_M).coordinates().get(0))

    inner_aoi = aoi.buffer(-3 * scale)
    clipped = ring.intersection(inner_aoi, cfg.SIMPLIFY_TOLERANCE_M)
    return _longest_component(clipped)


def _longest_component(geom: ee.Geometry) -> ee.Geometry:
    geom_type = geom.type().getInfo()
    if geom_type == "LineString":
        return geom
    parts = geom.coordinates().getInfo()  # список списков координат частей
    best = max(parts, key=lambda part: sum(
        ((part[i][0] - part[i - 1][0]) ** 2 + (part[i][1] - part[i - 1][1]) ** 2) ** 0.5
        for i in range(1, len(part))
    ))
    return ee.Geometry.LineString(best)


def extract_year(year: int, aoi: ee.Geometry, corridor: ee.Geometry) -> dict | None:
    composite, coll_id, n_scenes, window = build_year_composite(year, aoi)
    if composite is None:
        print(f"  {year}: нет сцен даже в расширенном окне {window} — пропуск")
        return None

    index_img = mndwi(composite, coll_id)
    # Оцу и векторизация — только в прибрежном коридоре (не всё открытое море),
    # и на укрупнённом масштабе: финальная линия всё равно проходит через
    # SIMPLIFY_TOLERANCE_M=10м и трансекты с шагом 500м, так что считать
    # гистограмму/векторизацию на нативных 10м Sentinel-2 избыточно дорого
    # без выигрыша в точности итогового результата.
    work_scale = max(_scale_for(coll_id), 30)
    threshold = otsu_threshold(index_img, corridor, scale=work_scale)
    threshold_val = threshold.getInfo()
    water_mask = index_img.gt(threshold)

    line = largest_water_ring(water_mask, corridor, scale=work_scale)
    coords = line.coordinates().getInfo()
    length_km = round(line.length(1).getInfo() / 1000, 1)

    return {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": [{
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {
                "year": year,
                "sensor": coll_id,
                "scale_m": _scale_for(coll_id),
                "n_scenes": n_scenes,
                "date_window": list(window),
                "otsu_threshold": round(threshold_val, 4),
                "data_quality": "good",
                "length_km": length_km,
            },
        }],
    }


def _scale_for(coll_id: str) -> int:
    from pipeline.gee.bands import COLLECTIONS
    return COLLECTIONS[coll_id]["scale_m"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", default="2000-2026")
    parser.add_argument("--out", default="pipeline/data/real/shorelines")
    parser.add_argument("--project", default="caspian-pulse-ee")
    args = parser.parse_args()

    ee.Initialize(project=args.project)
    aoi = ee.Geometry.Rectangle([
        cfg.AOI_MANGYSTAU["coordinates"][0][0][0], cfg.AOI_MANGYSTAU["coordinates"][0][0][1],
        cfg.AOI_MANGYSTAU["coordinates"][0][2][0], cfg.AOI_MANGYSTAU["coordinates"][0][2][1],
    ])

    corridor = coastal_corridor()
    years = parse_years(args.years)
    out_dir = Path(__file__).resolve().parents[2] / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    ok, failed = [], []
    for year in years:
        print(f"{year}: извлечение...")
        try:
            fc = extract_year(year, aoi, corridor)
        except Exception as e:
            print(f"  {year}: ОШИБКА — {e}")
            failed.append(year)
            continue
        if fc is None:
            failed.append(year)
            continue
        path = out_dir / f"shoreline_{year}.geojson"
        path.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
        props = fc["features"][0]["properties"]
        print(f"  {year}: OK, {props['n_scenes']} сцен, otsu={props['otsu_threshold']}, "
              f"{props['length_km']} км -> {path}")
        ok.append(year)

    print(f"\nГотово: {len(ok)} лет извлечено, {len(failed)} пропущено {failed}")


if __name__ == "__main__":
    main()
