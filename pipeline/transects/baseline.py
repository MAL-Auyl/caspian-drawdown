"""Baseline — опорная линия, от которой строятся перпендикулярные трансекты.

Строится из COAST_WAYPOINTS (сглаженная осевая линия побережья), а не из
векторизованной береговой линии конкретного года — так baseline не зависит
от качества MNDWI-векторизации и одинаков для всех лет. Точность самого
измерения при этом не страдает: она определяется прямым сэмплингом MNDWI
вдоль трансекты (см. pipeline/gee/sample_transects.py), а не геометрией
baseline.
"""
import json
from pathlib import Path

import pyproj
from shapely.geometry import LineString, shape
from shapely.ops import transform

from pipeline.gee import config as cfg

_TO_METRIC = pyproj.Transformer.from_crs(cfg.CRS_OUTPUT, cfg.CRS_METRIC, always_xy=True).transform
_TO_OUTPUT = pyproj.Transformer.from_crs(cfg.CRS_METRIC, cfg.CRS_OUTPUT, always_xy=True).transform


def waypoints_to_metric_line(waypoints: list | None = None) -> LineString:
    line_wgs84 = LineString(waypoints or cfg.COAST_WAYPOINTS)
    return transform(_TO_METRIC, line_wgs84)


def load_refined_waypoints(path: Path | str) -> list:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["waypoints"]


def build_baseline(offset_m: float = cfg.BASELINE_OFFSET_M, waypoints: list | None = None) -> LineString:
    """Смещаем осевую линию побережья перпендикулярно самой себе на offset_m
    в сторону суши, чтобы весь диапазон отступления берега укладывался
    по одну сторону от baseline.

    По умолчанию — грубые COAST_WAYPOINTS (9 точек). Если передан waypoints
    (например, из pipeline.transects.refine_baseline — уточнённая линия по
    уже измеренному берегу), используется он: даёт гладкую baseline и
    трансекты, реально расходящиеся веером по изгибу берега, а не частокол
    параллельных линий на каждом из 8 прямых отрезков грубой линии."""
    coast = waypoints_to_metric_line(waypoints)
    offset = coast.parallel_offset(offset_m, side="left", join_style=2)
    if offset.geom_type == "MultiLineString":
        offset = max(offset.geoms, key=lambda g: g.length)
    return offset


def load_shoreline_metric(path: Path) -> LineString:
    """Для обратной совместимости — загрузка векторизованной линии года,
    если она когда-то понадобится (например, для полноценной DSAS-карты
    после уточнения COAST_WAYPOINTS по OSM)."""
    fc = json.loads(path.read_text(encoding="utf-8"))
    geom = shape(fc["features"][0]["geometry"])
    return transform(_TO_METRIC, geom)
