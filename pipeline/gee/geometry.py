"""Прибрежный коридор для ограничения тяжёлых вычислений (Оцу, векторизация)."""
import ee

from pipeline.gee import config as cfg


def coastal_corridor() -> ee.Geometry:
    line = ee.Geometry.LineString(cfg.COAST_WAYPOINTS)
    return line.buffer(cfg.COASTAL_CORRIDOR_HALF_WIDTH_M)
