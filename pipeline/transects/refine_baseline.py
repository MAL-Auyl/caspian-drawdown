"""Перестраивает baseline из уже измеренной (и очищенной) линии берега,
а не из 9 грубых COAST_WAYPOINTS.

Зачем: перпендикуляры к кусочно-линейной 9-точечной baseline параллельны
друг другу на каждом из 8 прямых отрезков — не баг геометрии, а следствие
того, что опорная линия сама грубая. Baseline, построенная из реальной
(уже отфильтрованной) линии берега, повторяет её изгибы — трансекты
расходятся веером так, как и должны у DSAS.

Запуск:
    python3 -m pipeline.transects.refine_baseline --shoreline data/real/shorelines/shoreline_2026.geojson --out pipeline/data/manual/refined_baseline.json
"""
import argparse
import json
from pathlib import Path

import pyproj
from shapely.geometry import LineString, Point
from shapely.ops import transform

from pipeline.gee import config as cfg

REPO_ROOT = Path(__file__).resolve().parents[2]
_TO_METRIC = pyproj.Transformer.from_crs(cfg.CRS_OUTPUT, cfg.CRS_METRIC, always_xy=True).transform
_TO_OUTPUT = pyproj.Transformer.from_crs(cfg.CRS_METRIC, cfg.CRS_OUTPUT, always_xy=True).transform

SIMPLIFY_TOLERANCE_M = 300  # сглаживаем остаточный шум, сохраняя форму берега


def _enforce_monotonic_order(offset: LineString) -> LineString:
    """parallel_offset() ломается на резких изгибах/самопересечениях исходной
    линии (например, мыс порта Актау) — результат может пойти "назад" вдоль
    берега вместо плавного продолжения. Проецируем каждую точку на грубую
    9-точечную COAST_WAYPOINTS (она не изгибается достаточно резко, чтобы
    ломаться) и сортируем по этой проекции — гарантирует монотонность вдоль
    берега независимо от локальных артефактов offset."""
    coast_ref = transform(_TO_METRIC, LineString(cfg.COAST_WAYPOINTS))
    pts = list(offset.coords)
    pts_sorted = sorted(pts, key=lambda p: coast_ref.project(Point(p)))
    return LineString(pts_sorted)


def build_refined_baseline(shoreline_path: Path, offset_m: float = cfg.BASELINE_OFFSET_M) -> LineString:
    fc = json.loads(shoreline_path.read_text(encoding="utf-8"))
    coast_wgs84 = LineString(fc["features"][0]["geometry"]["coordinates"])
    coast_metric = transform(_TO_METRIC, coast_wgs84).simplify(SIMPLIFY_TOLERANCE_M)

    offset = coast_metric.parallel_offset(offset_m, side="left", join_style=2)
    if offset.geom_type == "MultiLineString":
        offset = max(offset.geoms, key=lambda g: g.length)
    return _enforce_monotonic_order(offset)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shoreline", default="data/real/shorelines/shoreline_2026.geojson")
    parser.add_argument("--out", default="pipeline/data/manual/refined_baseline.json")
    args = parser.parse_args()

    baseline = build_refined_baseline(REPO_ROOT / args.shoreline)
    baseline_wgs84 = transform(_TO_OUTPUT, baseline)
    waypoints = [list(c) for c in baseline_wgs84.coords]

    out_path = REPO_ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"waypoints": waypoints}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: refined baseline — {len(waypoints)} точек, "
          f"{round(baseline.length/1000,1)} км -> {out_path}")


if __name__ == "__main__":
    main()
