"""Корневая причина «кривых» линий на карте: трансекта идёт от объекта в
городе к морю и по пути может зацепить городской пруд/водоём — find_crossing
находит ПЕРВУЮ воду на луче, а не обязательно настоящее море.

Фильтр: для каждой трансекты считаем, где она в принципе ДОЛЖНА пересекать
берег (по грубой линии COAST_WAYPOINTS) — и любую найденную позицию, которая
далеко от этой ожидаемой точки, считаем ложным срабатыванием (пруд, лужа
после дождя на солончаке и т.п.), а не измерением моря.

Не требует повторного похода в Earth Engine — работает по уже сохранённым
позициям в transects.geojson.

Запуск:
    python3 -m pipeline.postprocess.filter_by_corridor --in data/processed
"""
import argparse
import json
from pathlib import Path

import pyproj
from shapely.geometry import LineString
from shapely.ops import transform

from pipeline.gee import config as cfg

REPO_ROOT = Path(__file__).resolve().parents[2]
_TO_METRIC = pyproj.Transformer.from_crs(cfg.CRS_OUTPUT, cfg.CRS_METRIC, always_xy=True).transform

TOLERANCE_M = 3000.0


def expected_distance(transect_metric: LineString, coast_metric: LineString) -> float | None:
    inter = transect_metric.intersection(coast_metric)
    if inter.is_empty:
        return None
    if inter.geom_type == "Point":
        return transect_metric.project(inter)
    # несколько пересечений (изогнутая COAST_WAYPOINTS) — берём ближайшее к началу
    pts = list(inter.geoms) if hasattr(inter, "geoms") else [inter]
    return min(transect_metric.project(p) for p in pts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_dir", default="data/processed")
    parser.add_argument("--tolerance", type=float, default=TOLERANCE_M)
    parser.add_argument("--waypoints", default=None,
                         help="JSON с ожидаемой линией берега (refine_baseline.py). "
                              "Без флага — грубые COAST_WAYPOINTS из config.py.")
    args = parser.parse_args()

    base = REPO_ROOT / args.in_dir
    path = base / "transects.geojson"
    fc = json.loads(path.read_text(encoding="utf-8"))

    if args.waypoints:
        from pipeline.transects.baseline import load_refined_waypoints
        waypoints = load_refined_waypoints(args.waypoints)
    else:
        waypoints = cfg.COAST_WAYPOINTS
    coast_metric = transform(_TO_METRIC, LineString(waypoints))

    total_nulled, transects_without_expected = 0, 0
    for f in fc["features"]:
        line_metric = transform(_TO_METRIC, LineString(f["geometry"]["coordinates"]))
        exp = expected_distance(line_metric, coast_metric)
        if exp is None:
            transects_without_expected += 1
            continue
        positions = f["properties"]["positions"]
        for y, v in positions.items():
            if v is None:
                continue
            if abs(abs(v) - exp) > args.tolerance:
                positions[y] = None
                total_nulled += 1

    path.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    print(f"OK: {total_nulled} позиций отброшено как вне коридора ожидаемого берега "
          f"(допуск {args.tolerance:.0f} м), {transects_without_expected} трансект без "
          f"пересечения с COAST_WAYPOINTS (не тронуты) -> {path}")


if __name__ == "__main__":
    main()
