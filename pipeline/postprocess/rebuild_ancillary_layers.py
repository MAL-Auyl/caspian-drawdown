"""Пересобирает dust_zones.geojson и exposed_seabed.geojson на РЕАЛЬНОЙ
геометрии (COAST_WAYPOINTS / координаты объектов), а не на синтетической
кривой мок-генератора — иначе эти слои визуально не совпадают с настоящим
берегом и трансектами после перехода на реальные данные.

Запуск:
    python3 -m pipeline.postprocess.rebuild_ancillary_layers --out data/processed
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import pyproj
from shapely.geometry import LineString
from shapely.ops import transform

from pipeline.gee import config as cfg
from pipeline.mock.generate import OBJECT_DEFS

REPO_ROOT = Path(__file__).resolve().parents[2]
_TO_METRIC = pyproj.Transformer.from_crs(cfg.CRS_OUTPUT, cfg.CRS_METRIC, always_xy=True).transform
_TO_OUTPUT = pyproj.Transformer.from_crs(cfg.CRS_METRIC, cfg.CRS_OUTPUT, always_xy=True).transform

RNG = np.random.default_rng(7)


def build_exposed_seabed(width_m: float = 2500) -> dict:
    """Полоса вдоль настоящей осевой линии побережья — не претендует на
    точную площадь осушенного дна (для этого нужна векторизация MNDWI-маски
    по годам), но геометрически совпадает с реальным берегом на карте."""
    coast_wgs84 = LineString(cfg.COAST_WAYPOINTS)
    coast_metric = transform(_TO_METRIC, coast_wgs84)
    strip = coast_metric.buffer(width_m, cap_style=2, join_style=2)
    strip_wgs84 = transform(_TO_OUTPUT, strip)

    if strip_wgs84.geom_type == "Polygon":
        rings = [list(strip_wgs84.exterior.coords)]
    else:
        rings = [list(max(strip_wgs84.geoms, key=lambda g: g.area).exterior.coords)]

    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": rings},
            "properties": {
                "area_km2": round(strip.area / 1e6, 1),
                "period": "2000-2026",
                "note": "Индикативная полоса вдоль побережья, не векторизация MNDWI-маски по годам",
            },
        }],
    }


def build_dust_zones() -> dict:
    """Розы ветров вокруг реального водозабора МАЭК (главный объект демо),
    а не произвольной точки."""
    center = next(od for od in OBJECT_DEFS if od["category"] == "water_supply")
    cx, cy = center["lon"], center["lat"]

    features = []
    for i, deg in enumerate(range(0, 360, 45)):
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/processed")
    args = parser.parse_args()
    out_dir = REPO_ROOT / args.out

    seabed = build_exposed_seabed()
    dust = build_dust_zones()
    (out_dir / "exposed_seabed.geojson").write_text(json.dumps(seabed, ensure_ascii=False), encoding="utf-8")
    (out_dir / "dust_zones.geojson").write_text(json.dumps(dust, ensure_ascii=False), encoding="utf-8")
    print(f"OK: exposed_seabed ({seabed['features'][0]['properties']['area_km2']} км²) "
          f"и dust_zones ({len(dust['features'])} секторов вокруг водозабора МАЭК) -> {out_dir}")


if __name__ == "__main__":
    main()
