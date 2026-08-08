"""Пересчитывает distance_to_shore_*_m в objects.geojson как настоящее
расстояние от точки объекта до линии берега конкретного года — без повторного
похода в Earth Engine (нужны уже посчитанные shorelines/shoreline_YYYY.geojson).

Грабля #7: раньше сюда напрямую писалось значение из
transects[].properties.positions — проекция точки пересечения на трансекту
ОТ ЕЁ НАЧАЛА (якорь на baseline, вынесенный от настоящего берега на
BASELINE_OFFSET_M), а не расстояние от объекта до берега. Для всех объектов
получались похожие ~4000м независимо от того, стоит объект у самой кромки
воды или в нескольких километрах — эта же ошибка попадала в компонент
"distance" риск-формулы (см. pipeline/risk/engine.py — там же был инвертирован
знак нормировки, тоже исправлено).

Запуск:
    python3 -m pipeline.postprocess.recompute_object_distances --in data/real_v2
"""
import argparse
import json
from pathlib import Path

import pyproj
from shapely.geometry import Point, shape
from shapely.ops import transform

from pipeline.gee import config as cfg
from pipeline.risk.engine import compute_risk
from pipeline.forecast.scenarios import build_scenarios

REPO_ROOT = Path(__file__).resolve().parents[2]
_TO_METRIC = pyproj.Transformer.from_crs(cfg.CRS_OUTPUT, cfg.CRS_METRIC, always_xy=True).transform


def _distance_to_shoreline(lon: float, lat: float, year: int, shorelines_dir: Path, years: list[int]) -> float:
    candidates = sorted(years, key=lambda y: abs(y - year))
    for y in candidates:
        path = shorelines_dir / f"shoreline_{y}.geojson"
        if not path.exists():
            continue
        fc = json.loads(path.read_text(encoding="utf-8"))
        if not fc["features"]:
            continue
        coast_metric = transform(_TO_METRIC, shape(fc["features"][0]["geometry"]))
        pt_metric = transform(_TO_METRIC, Point(lon, lat))
        return coast_metric.distance(pt_metric)
    return 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_dir", default="data/real_v2")
    args = parser.parse_args()
    base = REPO_ROOT / args.in_dir

    shorelines_dir = base / "shorelines"
    years = sorted(int(p.stem.split("_")[1]) for p in shorelines_dir.glob("shoreline_*.geojson"))
    last_year = years[-1]

    path = base / "objects.geojson"
    fc = json.loads(path.read_text(encoding="utf-8"))

    for f in fc["features"]:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        speed = p["speed_m_per_year"]

        d2000 = _distance_to_shoreline(lon, lat, 2000, shorelines_dir, years)
        d2010 = _distance_to_shoreline(lon, lat, 2010, shorelines_dir, years)
        d2020 = _distance_to_shoreline(lon, lat, 2020, shorelines_dir, years)
        d2026 = _distance_to_shoreline(lon, lat, 2026, shorelines_dir, years)

        risk = compute_risk(speed, d2026, p["category"])
        forecast = build_scenarios(d2026, speed, last_year)

        old_d2026 = p["distance_to_shore_2026_m"]
        p["distance_to_shore_2000_m"] = round(d2000, 1)
        p["distance_to_shore_2010_m"] = round(d2010, 1)
        p["distance_to_shore_2020_m"] = round(d2020, 1)
        p["distance_to_shore_2026_m"] = round(d2026, 1)
        p["criticality"] = risk["criticality"]
        p["risk_score"] = risk["score"]
        p["risk_level"] = risk["level"]
        p["risk_components"] = risk["components"]
        p["forecast"] = forecast

        print(f"{p['name_ru'][:28]:30s} 2026: {old_d2026:8.1f} -> {d2026:8.1f}   risk={risk['score']} ({risk['level']})")

    path.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    print(f"\nOK -> {path}")


if __name__ == "__main__":
    main()
