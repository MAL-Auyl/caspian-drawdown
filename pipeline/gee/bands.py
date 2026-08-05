"""Схемы каналов и коэффициенты масштабирования по коллекциям.

Landsat Collection 2 Level-2 хранит SR как целые DN; физическое отражение —
DN * scale + offset (см. USGS LSDS-1619). Sentinel-2 SR хранит отражение
как DN/10000.
"""

LANDSAT_SR_SCALE = 0.0000275
LANDSAT_SR_OFFSET = -0.2
S2_SR_SCALE = 0.0001

COLLECTIONS = {
    "LANDSAT/LT05/C02/T1_L2": {
        "kind": "landsat", "green": "SR_B2", "swir": "SR_B5", "nir": "SR_B4", "qa": "QA_PIXEL", "scale_m": 30,
    },
    "LANDSAT/LE07/C02/T1_L2": {
        "kind": "landsat", "green": "SR_B2", "swir": "SR_B5", "nir": "SR_B4", "qa": "QA_PIXEL", "scale_m": 30,
    },
    "LANDSAT/LC08/C02/T1_L2": {
        "kind": "landsat", "green": "SR_B3", "swir": "SR_B6", "nir": "SR_B5", "qa": "QA_PIXEL", "scale_m": 30,
    },
    "LANDSAT/LC09/C02/T1_L2": {
        "kind": "landsat", "green": "SR_B3", "swir": "SR_B6", "nir": "SR_B5", "qa": "QA_PIXEL", "scale_m": 30,
    },
    "COPERNICUS/S2_SR_HARMONIZED": {
        "kind": "sentinel2", "green": "B3", "swir": "B11", "nir": "B8", "qa": "QA60", "scale_m": 10,
    },
}

# Городские поверхности (асфальт, тени, промзона) отражают в NIR заметно
# сильнее воды — используем как второе условие поверх MNDWI, чтобы не
# принимать тёмные городские пятна за воду (см. docs/00_DECISIONS.md).
NIR_WATER_MAX = 0.15


def collection_for_year(year: int) -> str:
    """Выбор коллекции по году — линия соответствует данным, реально
    доступным по годам (Landsat 5 закрыт в 2011/2012, Landsat 8 — с 2013,
    Sentinel-2 даёт устойчивое покрытие AOI с 2016)."""
    if year <= 2011:
        return "LANDSAT/LT05/C02/T1_L2"
    if 2013 <= year <= 2015:
        return "LANDSAT/LC08/C02/T1_L2"
    return "COPERNICUS/S2_SR_HARMONIZED"
