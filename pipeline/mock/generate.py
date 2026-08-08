"""Генератор синтетических данных правильной схемы для фронтенда/бэкенда.

Смысл: пока пайплайн GEE ещё не готов, фронтенд и бэкенд работают на
данных ровно той структуры, что будет в проде — включая объём (447
трансект, 26 срезов береговой линии, 8 объектов). Числа не претендуют
на точность: они лишь правдоподобны и внутренне согласованы (скорость
отступления <-> траектория positions <-> риск <-> прогноз).

Запуск:
    python3 -m pipeline.mock.generate --out data/processed
"""
import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pipeline.gee import config as cfg
from pipeline.common.stats import confidence_of, regression_for, risk_class_of
from pipeline.risk.engine import compute_risk
from pipeline.forecast.scenarios import build_scenarios

RNG = np.random.default_rng(42)

COAST_LOCATIONS = [
    "Севернее водозабора МАЭК", "Бухта Курык", "Тюб-Караганский залив",
    "Мыс Меловой", "Южная коса Актау", "Побережье у Баутино",
    "Залив Комсомолец", "Мыс Ракушечный", "Северный Бузачи",
    "Прибрежная зона Каламкас",
]

OBJECT_DEFS = [
    dict(object_id=1, name_ru="Водозаборный канал МАЭК",
         name_kk="МАЭК су қабылдау арнасы", name_en="MAEK Water Intake Channel",
         category="water_supply", criticality=10, lon=51.2806, lat=43.5995,
         description_ru="Обеспечивает забор морской воды для опреснения. Питьевая вода Актау.",
         description_kk="Тұщыландыруға теңіз суын алуды қамтамасыз етеді.",
         description_en="Supplies seawater for desalination — Aktau's drinking water.",
         recommendation_ru="Требуется план поэтапного удлинения канала. Дноуглубление даёт временный эффект.",
         recommendation_en="Phased channel extension plan required; dredging is a temporary measure."),
    dict(object_id=2, name_ru="Энергоблоки МАЭК",
         name_kk="МАЭК энергоблоктары", name_en="MAEK Power Units",
         category="energy", criticality=9, lon=51.2806, lat=43.6105,
         description_ru="Тепловая и электрическая генерация, зависит от водозабора.",
         description_kk="Су қабылдауға тәуелді жылу және электр генерациясы.",
         description_en="Thermal and electric generation, dependent on the water intake.",
         recommendation_ru="Мониторинг совместно с водозаборным каналом.",
         recommendation_en="Monitor jointly with the intake channel."),
    dict(object_id=3, name_ru="Порт Актау",
         name_kk="Ақтау порты", name_en="Port of Aktau",
         category="port", criticality=8, lon=51.2207, lat=43.6018,
         description_ru="Основной морской порт региона, грузовые и паромные перевозки.",
         description_kk="Аймақтың негізгі теңіз порты.",
         description_en="The region's main seaport, cargo and ferry traffic.",
         recommendation_ru="Периодический промер глубин на подходных каналах.",
         recommendation_en="Periodic depth surveys on approach channels."),
    dict(object_id=4, name_ru="Порт Баутино",
         name_kk="Баутино порты", name_en="Port of Bautino",
         category="port", criticality=7, lon=50.2487, lat=44.5482,
         description_ru="Вспомогательный порт на полуострове Тюб-Караган.",
         description_kk="Түпқараған түбегіндегі қосалқы порт.",
         description_en="Auxiliary port on the Tyub-Karagan peninsula.",
         recommendation_ru="Отслеживать обмеление подходного канала.",
         recommendation_en="Track shoaling of the approach channel."),
    dict(object_id=6, name_ru="Городской пляж",
         name_kk="Қалалық жағажай", name_en="City Beach",
         category="recreation", criticality=3, lon=51.196, lat=43.624,
         description_ru="Основной пляж города, сезонная нагрузка.",
         description_kk="Қаланың негізгі жағажайы.",
         description_en="The city's main beach, seasonal use.",
         recommendation_ru="Мониторинг ширины пляжной полосы.",
         recommendation_en="Monitor beach-strip width."),
    dict(object_id=7, name_ru="Rixos Water World Aktau",
         name_kk="Rixos Water World Aktau", name_en="Rixos Water World Aktau",
         category="tourism", criticality=4, lon=51.2973, lat=43.5066,
         description_ru="Курортный комплекс, площадка финала хакатона.",
         description_kk="Курорттық кешен, хакатон финалының алаңы.",
         description_en="Resort complex, hackathon final venue.",
         recommendation_ru="Долгосрочное планирование береговой инфраструктуры курорта.",
         recommendation_en="Long-term planning for the resort's shore infrastructure."),
]


def coast_point(t: float) -> tuple[float, float]:
    """Параметрическая синтетическая осевая линия побережья, t in [0,1]."""
    lat = 42.70 + 2.35 * t + 0.12 * math.sin(7 * math.pi * t)
    lon = 51.10 + 0.55 * math.sin(2.4 * math.pi * t) - 0.35 * t
    return lon, lat


def coast_tangent(t: float, eps: float = 1e-4) -> tuple[float, float]:
    x0, y0 = coast_point(max(t - eps, 0.0))
    x1, y1 = coast_point(min(t + eps, 1.0))
    dx, dy = x1 - x0, y1 - y0
    norm = math.hypot(dx, dy) or 1.0
    return dx / norm, dy / norm


def build_transects(n: int):
    """n станций вдоль побережья + перпендикулярная геометрия."""
    ts = np.linspace(0.02, 0.98, n)
    transects = []
    for i, t in enumerate(ts):
        lon, lat = coast_point(t)
        tx, ty = coast_tangent(t)
        nx, ny = -ty, tx  # нормаль (перпендикуляр к берегу)
        half_len_deg = 0.045  # ~5 км в наших широтах, для визуализации достаточно
        p0 = (lon - nx * half_len_deg * 0.2, lat - ny * half_len_deg * 0.2)
        p1 = (lon + nx * half_len_deg, lat + ny * half_len_deg)
        transects.append({
            "transect_id": i + 1,
            "t": t,
            "anchor": (lon, lat),
            "line": [p0, p1],
            "baseline_distance_m": round(t * cfg.TRANSECT_COUNT * cfg.TRANSECT_SPACING_M, 1),
        })
    return transects


def synth_speed(i: int, n: int) -> float:
    """Скорость отступления, м/год. Отрицательная = отступление."""
    base = RNG.normal(loc=-12.4, scale=8.9)
    # немного пространственной корреляции: соседние трансекты похожи
    base += 3.0 * math.sin(2 * math.pi * i / max(n, 1) * 5)
    if i == 310:  # держим один явный "рекордный" сегмент, как в статистике
        base = -47.2
    return float(np.clip(base, -58.0, 4.5))


def build_transect_features(transects, years):
    features = []
    for j, tr in enumerate(transects):
        speed = synth_speed(j, len(transects))
        p0 = float(RNG.uniform(10_000, 16_000))
        positions = {}
        for y in years:
            if y in cfg.MISSING_YEARS:
                positions[y] = None
                continue
            noise = float(RNG.normal(0, 4.0))
            positions[y] = round(p0 + speed * (y - years[0]) + noise, 1)

        reg = regression_for(years, positions)
        valid_years = reg["n"]
        first_y = years[0]
        last_y = years[-1]
        total_retreat = round(positions[first_y] - positions[last_y], 1)
        conf = confidence_of(reg["r_squared"], valid_years)

        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [list(tr["line"][0]), list(tr["line"][1])]},
            "properties": {
                "transect_id": tr["transect_id"],
                "baseline_distance_m": tr["baseline_distance_m"],
                "positions": {str(y): positions[y] for y in years},
                "total_retreat_m": total_retreat,
                "speed_m_per_year": reg["slope_m_per_year"],
                "r_squared": reg["r_squared"],
                "std_error": reg["std_error"],
                "ci_95_low": reg["ci_95_low"],
                "ci_95_high": reg["ci_95_high"],
                "valid_years": valid_years,
                "confidence": conf,
                "risk_class": risk_class_of(reg["slope_m_per_year"]),
                "location_ru": COAST_LOCATIONS[j % len(COAST_LOCATIONS)],
                "anchor": list(tr["anchor"]),
            },
        })
    return features


def nearest_transect(lon, lat, transect_features):
    best, best_d = None, float("inf")
    for f in transect_features:
        ax, ay = f["properties"]["anchor"]
        d = math.hypot(ax - lon, ay - lat)
        if d < best_d:
            best, best_d = f, d
    approx_m = best_d * 96_000  # грубый градус->метр для широты ~43.5°
    return best, approx_m


def build_objects(transect_features, years):
    features = []
    for od in OBJECT_DEFS:
        tf, dist_m = nearest_transect(od["lon"], od["lat"], transect_features)
        speed = tf["properties"]["speed_m_per_year"]

        d2000 = float(RNG.uniform(120, 500))
        years_span = years[-1] - years[0]
        d2026 = round(d2000 + abs(speed) * years_span * float(RNG.uniform(0.7, 1.1)), 1)
        d2010 = round(d2000 + (d2026 - d2000) * (2010 - years[0]) / years_span, 1)
        d2020 = round(d2000 + (d2026 - d2000) * (2020 - years[0]) / years_span, 1)

        risk = compute_risk(speed, d2026, od["category"])
        forecast = build_scenarios(d2026, speed, years[-1])

        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [od["lon"], od["lat"]]},
            "properties": {
                "object_id": od["object_id"],
                "name_ru": od["name_ru"], "name_kk": od["name_kk"], "name_en": od["name_en"],
                "category": od["category"], "criticality": risk["criticality"],
                "nearest_transect_id": tf["properties"]["transect_id"],
                "distance_to_shore_2000_m": round(d2000, 1),
                "distance_to_shore_2010_m": d2010,
                "distance_to_shore_2020_m": d2020,
                "distance_to_shore_2026_m": d2026,
                "speed_m_per_year": speed,
                "risk_score": risk["score"],
                "risk_level": risk["level"],
                "risk_components": risk["components"],
                "forecast": forecast,
                "description_ru": od["description_ru"], "description_kk": od["description_kk"], "description_en": od["description_en"],
                "recommendation_ru": od["recommendation_ru"], "recommendation_en": od["recommendation_en"],
                "source": "mock — заменяется реальными данными после расчёта на снимках",
            },
        })
    return features


def build_shorelines(years):
    """Один LineString на год; линия сдвигается перпендикулярно берегу
    пропорционально накопленному среднему отступлению — чисто для наглядности слайдера."""
    ts = np.linspace(0.0, 1.0, 300)
    out = {}
    cum = 0.0
    for y in years:
        if y in cfg.MISSING_YEARS:
            continue
        cum += 12.4 / 96_000  # средняя скорость в градусах/год, грубая оценка
        coords = []
        for t in ts:
            lon, lat = coast_point(t)
            tx, ty = coast_tangent(t)
            nx, ny = -ty, tx
            coords.append([round(lon + nx * cum, 5), round(lat + ny * cum, 5)])
        out[y] = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": [{
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": {
                    "year": y,
                    "sensor": "LANDSAT/LT05" if y < 2013 else ("LANDSAT/LC08" if y < 2016 else "COPERNICUS/S2_SR_HARMONIZED"),
                    "scale_m": 30 if y < 2016 else 10,
                    "acquisition_date": f"{y}-07-{10 + (y % 15):02d}",
                    "cloud_pct": round(float(RNG.uniform(0.5, 9.5)), 1),
                    "wind_ms": round(float(RNG.uniform(2.0, 7.5)), 1),
                    "otsu_threshold": round(float(RNG.uniform(0.06, 0.14)), 3),
                    "data_quality": "good",
                    "length_km": 218.4,
                },
            }],
        }
    return out


def build_dust_zones():
    sectors = list(range(0, 360, 45))
    features = []
    for i, deg in enumerate(sectors):
        cx, cy = 51.0, 43.9
        rad = math.radians(deg)
        r_in, r_out = 0.05, 0.25
        p1 = (cx + r_in * math.sin(rad), cy + r_in * math.cos(rad))
        p2 = (cx + r_out * math.sin(rad), cy + r_out * math.cos(rad))
        p3 = (cx + r_out * math.sin(rad + 0.7), cy + r_out * math.cos(rad + 0.7))
        p4 = (cx + r_in * math.sin(rad + 0.7), cy + r_in * math.cos(rad + 0.7))
        freq = round(float(RNG.uniform(0.05, 0.22)), 2)
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[list(p1), list(p2), list(p3), list(p4), list(p1)]]},
            "properties": {
                "zone_id": i + 1, "sector_deg": deg, "frequency": freq,
                "risk_level": "high" if freq > 0.17 else "medium" if freq > 0.1 else "low",
                "distance_km": round(r_out * 96, 1),
            },
        })
    return {"type": "FeatureCollection", "features": features}


def build_exposed_seabed():
    ts = np.linspace(0.0, 1.0, 200)
    outer = []
    for t in ts:
        lon, lat = coast_point(t)
        tx, ty = coast_tangent(t)
        nx, ny = -ty, tx
        outer.append([lon + nx * 0.03, lat + ny * 0.03])
    inner = []
    for t in ts[::-1]:
        lon, lat = coast_point(t)
        tx, ty = coast_tangent(t)
        nx, ny = -ty, tx
        inner.append([lon, lat])
    ring = outer + inner + [outer[0]]
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[round(x, 5), round(y, 5)] for x, y in ring]]},
            "properties": {"area_km2": 84.6, "period": "2000-2026"},
        }],
    }


def build_statistics(transect_features, object_features, years):
    speeds = [f["properties"]["speed_m_per_year"] for f in transect_features]
    by_conf = {"high": 0, "medium": 0, "low": 0}
    for f in transect_features:
        by_conf[f["properties"]["confidence"]] += 1
    risk_levels = [f["properties"]["risk_level"] for f in object_features]
    max_i = int(np.argmin(speeds))
    return {
        "generated_at": "2026-08-05T00:00:00Z",
        "data_version": "mock-2026-08-05",
        "region": "Mangystau",
        "period": {"from": years[0], "to": years[-1], "years_analyzed": len(years) - len(cfg.MISSING_YEARS), "missing": cfg.MISSING_YEARS},
        "coastline": {
            "length_analyzed_km": 218.4,
            "transects_total": len(transect_features),
            "by_confidence": by_conf,
        },
        "retreat": {
            "mean_speed_m_per_year": round(float(np.mean(speeds)), 1),
            "median_speed_m_per_year": round(float(np.median(speeds)), 1),
            "std_speed": round(float(np.std(speeds)), 1),
            "max_speed_m_per_year": round(float(np.min(speeds)), 1),
            "max_speed_transect_id": transect_features[max_i]["properties"]["transect_id"],
            "total_mean_retreat_m": round(float(np.mean([f["properties"]["total_retreat_m"] for f in transect_features])), 1),
        },
        "exposed_seabed_km2": 84.6,
        "objects": {
            "total": len(object_features),
            "high_risk": risk_levels.count("high"),
            "medium_risk": risk_levels.count("medium"),
            "low_risk": risk_levels.count("low"),
        },
        "validation": {"rmse_m": None, "sites": 3, "control_transects": 60, "note": "заполняется backtest-модулем на реальных данных"},
        "yearly_trend": [
            {"year": y, "mean_position_m": None}
            for y in years
        ],
    }


def build_meta():
    return {
        "app": "Caspian Pulse",
        "version": "0.1.0-mock",
        "data_version": "mock-2026-08-05",
        "methodology": {
            "water_index": "MNDWI",
            "threshold_method": "Otsu",
            "shoreline_method": "DSAS-style transects, 500 m spacing",
            "forecast_model": "OLS linear regression + 2nd degree polynomial",
            "crs_metric": cfg.CRS_METRIC,
            "validation_rmse_m": None,
            "validation_sites": 3,
        },
        "sources": [
            {"name": "Landsat 5/7/8/9 Collection 2 L2", "provider": "USGS", "license": "Public Domain"},
            {"name": "Sentinel-2 MSI L2A", "provider": "ESA Copernicus", "license": "Open"},
            {"name": "Open-Meteo Historical Archive", "provider": "Open-Meteo", "license": "CC BY 4.0"},
            {"name": "OpenStreetMap", "provider": "OSM Contributors", "license": "ODbL"},
        ],
        "disclaimer": {
            "ru": "Аналитический инструмент поддержки решений. Не заменяет официальные гидрографические и инженерные изыскания.",
        },
        "is_mock": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/processed")
    parser.add_argument("--fallback", default="frontend/public/fallback")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    out_dir = root / args.out
    (out_dir / "shorelines").mkdir(parents=True, exist_ok=True)

    years = cfg.YEARS
    transects_raw = build_transects(cfg.TRANSECT_COUNT)
    transect_features = build_transect_features(transects_raw, years)
    object_features = build_objects(transect_features, years)
    shorelines = build_shorelines(years)
    dust = build_dust_zones()
    seabed = build_exposed_seabed()
    stats_json = build_statistics(transect_features, object_features, years)
    meta = build_meta()

    for y, fc in shorelines.items():
        (out_dir / "shorelines" / f"shoreline_{y}.geojson").write_text(
            json.dumps(fc, ensure_ascii=False), encoding="utf-8")

    transects_fc = {"type": "FeatureCollection", "features": transect_features}
    objects_fc = {"type": "FeatureCollection", "features": object_features}

    (out_dir / "transects.geojson").write_text(json.dumps(transects_fc, ensure_ascii=False), encoding="utf-8")
    (out_dir / "objects.geojson").write_text(json.dumps(objects_fc, ensure_ascii=False), encoding="utf-8")
    (out_dir / "dust_zones.geojson").write_text(json.dumps(dust, ensure_ascii=False), encoding="utf-8")
    (out_dir / "exposed_seabed.geojson").write_text(json.dumps(seabed, ensure_ascii=False), encoding="utf-8")
    (out_dir / "statistics.json").write_text(json.dumps(stats_json, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    fallback_dir = root / args.fallback
    fallback_dir.mkdir(parents=True, exist_ok=True)
    bootstrap = {
        "meta": {**meta, "years": years, "missing_years": cfg.MISSING_YEARS,
                 "crs_metric": cfg.CRS_METRIC, "crs_output": cfg.CRS_OUTPUT,
                 "transect_spacing_m": cfg.TRANSECT_SPACING_M, "region": "Mangystau, Kazakhstan"},
        "shorelines": {str(y): fc for y, fc in shorelines.items()},
        "transects": transects_fc,
        "objects": objects_fc,
        "dust_zones": dust,
        "exposed_seabed": seabed,
        "statistics": stats_json,
    }
    (fallback_dir / "bootstrap.json").write_text(json.dumps(bootstrap, ensure_ascii=False), encoding="utf-8")

    print(f"OK: {len(transect_features)} transects, {len(shorelines)} shoreline years, "
          f"{len(object_features)} objects -> {out_dir}")


if __name__ == "__main__":
    main()
