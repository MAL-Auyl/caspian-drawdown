"""Перестраивает shoreline_YYYY.geojson из уже собранных позиций трансект —
без повторного обращения к Earth Engine.

Грабля #5 (обнаружена после интеграции в веб): линия берега на карте
зигзагит. Причина — линия строилась из сырых точек пересечения по годам,
а не из отфильтрованных: Hampel-фильтр в pipeline/common/stats.py защищает
только регрессию скорости в transects.geojson, а не саму геометрию линии.
Здесь — тот же принцип, но по соседям ВДОЛЬ БЕРЕГА (не по годам для одной
трансекты): единичная трансекта с аномальным расстоянием на фоне соседей
сглаживается или отбрасывается.

Запуск:
    python3 -m pipeline.postprocess.rebuild_shorelines --in data/processed
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pyproj
from shapely.geometry import LineString, Point
from shapely.ops import transform

from pipeline.gee import config as cfg

REPO_ROOT = Path(__file__).resolve().parents[2]
_TO_METRIC = pyproj.Transformer.from_crs(cfg.CRS_OUTPUT, cfg.CRS_METRIC, always_xy=True).transform
_TO_OUTPUT = pyproj.Transformer.from_crs(cfg.CRS_METRIC, cfg.CRS_OUTPUT, always_xy=True).transform

WINDOW = 5
HAMPEL_K = 3.0
FLOOR_M = 800.0


def spatial_filter(ordered_distances: list[float]) -> list[float | None]:
    """Точки, сильно отличающиеся от локальной медианы соседей вдоль берега,
    заменяются на None (пропуск в линии) вместо того, чтобы давать скачок."""
    n = len(ordered_distances)
    out = list(ordered_distances)
    for i in range(n):
        lo, hi = max(0, i - WINDOW), min(n, i + WINDOW + 1)
        neighborhood = [ordered_distances[j] for j in range(lo, hi) if j != i]
        if len(neighborhood) < 3:
            continue
        med = float(np.median(neighborhood))
        mad = float(np.median(np.abs(np.array(neighborhood) - med)))
        threshold = max(HAMPEL_K * 1.4826 * mad, FLOOR_M)
        if abs(ordered_distances[i] - med) > threshold:
            out[i] = None
    return out


def rebuild(base: Path):
    transects = json.loads((base / "transects.geojson").read_text(encoding="utf-8"))["features"]
    transects.sort(key=lambda f: f["properties"]["transect_id"])

    metric_lines = [transform(_TO_METRIC, LineString(f["geometry"]["coordinates"])) for f in transects]
    years = [y for y in cfg.YEARS if y not in cfg.MISSING_YEARS]

    out_dir = base / "shorelines"
    out_dir.mkdir(parents=True, exist_ok=True)
    written, skipped = 0, 0

    for year in years:
        raw = [f["properties"]["positions"].get(str(year)) for f in transects]
        distances = [abs(v) if v is not None else None for v in raw]

        valid_idx = [i for i, d in enumerate(distances) if d is not None]
        if len(valid_idx) < 2:
            skipped += 1
            continue
        valid_distances = [distances[i] for i in valid_idx]
        filtered = spatial_filter(valid_distances)

        coords = []
        for idx, d in zip(valid_idx, filtered):
            if d is None:
                continue
            pt_metric = metric_lines[idx].interpolate(d)
            coords.append(list(transform(_TO_OUTPUT, pt_metric).coords)[0])

        if len(coords) < 2:
            skipped += 1
            continue

        n_removed = sum(1 for d in filtered if d is None)
        fc = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": [{
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": {
                    "year": year, "data_quality": "good",
                    "length_km": round(LineString(coords).length * 96, 1),
                    "spatial_outliers_removed": n_removed,
                },
            }],
        }
        (out_dir / f"shoreline_{year}.geojson").write_text(
            json.dumps(fc, ensure_ascii=False), encoding="utf-8")
        written += 1
        print(f"  {year}: {len(coords)} точек, {n_removed} выбросов убрано")

    print(f"\nOK: {written} лет перестроено, {skipped} пропущено -> {out_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_dir", default="data/processed")
    args = parser.parse_args()
    rebuild(REPO_ROOT / args.in_dir)


if __name__ == "__main__":
    main()
