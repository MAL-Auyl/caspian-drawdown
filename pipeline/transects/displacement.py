"""Сборка записи трансекты: регрессия по позициям + метаданные.

Позиции по годам приходят готовыми из pipeline/gee/sample_transects.py
(прямой сэмплинг MNDWI вдоль луча) — здесь только статистика поверх них.
"""
from shapely.geometry import LineString

from pipeline.common.stats import confidence_of, regression_for, risk_class_of


def build_transect_record(transect_id: int, transect: LineString, positions: dict[int, float | None],
                           years: list[int], location_ru: str = "") -> dict:
    reg = regression_for(years, positions)
    valid = [y for y in years if positions.get(y) is not None]
    total_retreat = None
    if len(valid) >= 2:
        total_retreat = round(positions[valid[0]] - positions[valid[-1]], 1)

    conf = confidence_of(reg["r_squared"], reg["n"])
    return {
        "transect_id": transect_id,
        "geometry_metric": transect,
        "positions": positions,
        "total_retreat_m": total_retreat,
        "speed_m_per_year": reg["slope_m_per_year"],
        "r_squared": reg["r_squared"],
        "std_error": reg["std_error"],
        "ci_95_low": reg["ci_95_low"],
        "ci_95_high": reg["ci_95_high"],
        "valid_years": reg["n"],
        "confidence": conf,
        "risk_class": risk_class_of(reg["slope_m_per_year"]),
        "location_ru": location_ru,
    }
