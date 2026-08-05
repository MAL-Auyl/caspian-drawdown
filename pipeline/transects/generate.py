"""Трансекты DSAS: перпендикуляры к baseline с фиксированным шагом.

Грабля #1 из прошлого прогона: без явной проверки трансекты периодически
уходят в сушу вместо моря (знак нормали зависит от направления обхода
координат линии, а он не гарантирован). Направление здесь не решается
геометрически — оно проверяется по реальным пикселям MNDWI в
pipeline/gee/run_real_pipeline.py (какая сторона нормали реально идёт
от суши к воде), а эта функция лишь строит трансекты в заданную сторону.
"""
import math

from shapely.geometry import LineString

from pipeline.gee import config as cfg


class TransectDirectionError(RuntimeError):
    pass


def _tangent(coords, i):
    a = coords[max(i - 1, 0)]
    b = coords[min(i + 1, len(coords) - 1)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    norm = math.hypot(dx, dy) or 1.0
    return dx / norm, dy / norm


def cast_transects(baseline: LineString, sign: int) -> list[LineString]:
    length = baseline.length
    n = int(length // cfg.TRANSECT_SPACING_M)
    coords = list(baseline.coords)
    transects = []
    for i in range(n + 1):
        d = i * cfg.TRANSECT_SPACING_M
        point = baseline.interpolate(d)
        idx = min(int(d / (length / max(len(coords) - 1, 1))), len(coords) - 1)
        tx, ty = _tangent(coords, idx)
        nx, ny = -ty * sign, tx * sign
        p0 = (point.x, point.y)
        p1 = (point.x + nx * cfg.TRANSECT_LENGTH_M, point.y + ny * cfg.TRANSECT_LENGTH_M)
        transects.append(LineString([p0, p1]))
    return transects
