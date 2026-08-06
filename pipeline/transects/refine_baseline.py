"""
Перестраивает baseline из реальной линии берега с плавным веерным сглаживанием.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pyproj
from scipy.signal import savgol_filter
from shapely.geometry import LineString
from shapely.ops import transform

from pipeline.gee import config as cfg

REPO_ROOT = Path(__file__).resolve().parents[2]
_TO_METRIC = pyproj.Transformer.from_crs(cfg.CRS_OUTPUT, cfg.CRS_METRIC, always_xy=True).transform
_TO_OUTPUT = pyproj.Transformer.from_crs(cfg.CRS_METRIC, cfg.CRS_OUTPUT, always_xy=True).transform

# 1. Уменьшаем допуск генерализации с 300м до 30м, чтобы сохранить геометрию заливов
SIMPLIFY_TOLERANCE_M = 30  


def smooth_line_metric(line_metric: LineString, window_m: float = 500.0) -> LineString:
    """Уплотняет и сглаживает метрическую линию фильтром Савицкого-Голея."""
    length = line_metric.length
    # Интерполяция каждые 20 метров
    distances = np.arange(0, length, 20.0)
    pts = np.array([(line_metric.interpolate(d).x, line_metric.interpolate(d).y) for d in distances])
    
    # Расчет размера окна в точках
    window_pts = int(window_m / 20.0)
    if window_pts % 2 == 0:
        window_pts += 1
    if window_pts > len(pts):
        window_pts = len(pts) - 1 if len(pts) % 2 != 0 else len(pts) - 2

    if window_pts >= 5:
        smooth_x = savgol_filter(pts[:, 0], window_length=window_pts, polyorder=3)
        smooth_y = savgol_filter(pts[:, 1], window_length=window_pts, polyorder=3)
        return LineString(np.column_stack((smooth_x, smooth_y)))
    return LineString(pts)


def build_refined_baseline(shoreline_path: Path, offset_m: float = cfg.BASELINE_OFFSET_M) -> LineString:
    fc = json.loads(shoreline_path.read_text(encoding="utf-8"))
    coast_wgs84 = LineString(fc["features"][0]["geometry"]["coordinates"])
    
    # Упрощаем с мягким допуском (30м вместо 300м)
    coast_metric = transform(_TO_METRIC, coast_wgs84).simplify(SIMPLIFY_TOLERANCE_M)
    
    # Сглаживаем перед смещением (join_style=1 делаем закругленные углы вместо ломаных)
    smooth_coast = smooth_line_metric(coast_metric, window_m=600.0)
    offset = smooth_coast.parallel_offset(offset_m, side="left", join_style=1)
    
    if offset.geom_type == "MultiLineString":
        offset = max(offset.geoms, key=lambda g: g.length)
        
    # Итоговое сглаживание самой baseline
    return smooth_line_metric(offset, window_m=800.0)


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