"""Общий конфиг пайплайна: регион, проекции, параметры трансект."""

AOI_MANGYSTAU = {
    "type": "Polygon",
    "coordinates": [[
        [50.20, 42.55], [52.90, 42.55],
        [52.90, 45.40], [50.20, 45.40], [50.20, 42.55],
    ]],
}

CRS_METRIC = "EPSG:32639"   # UTM 39N — все расчёты расстояний
CRS_OUTPUT = "EPSG:4326"    # WGS84 — то, что уходит в API/фронтенд

YEARS = list(range(2000, 2027))
MISSING_YEARS = [2012]      # Landsat 5 закрыт, Landsat 8 ещё не запущен
MONTH = 7                   # только июль — минимум сгонно-нагонных искажений
MAX_CLOUD_PCT = 10
MAX_WIND_MS = 8.0

TRANSECT_SPACING_M = 500
TRANSECT_LENGTH_M = 15000
TRANSECT_COUNT = 447
BASELINE_OFFSET_M = 2000
SIMPLIFY_TOLERANCE_M = 10

WATER_METHOD = "otsu"       # "otsu" | "rf" — переключатель классификатора (модуль 2)

CRITICAL_DISTANCE_M = {
    "water_supply": 300,
    "energy": 400,
    "port": 200,
    "industry": 500,
    "transport": 150,
    "tourism": 100,
    "recreation": 100,
}

CATEGORY_CRITICALITY = {
    "water_supply": {"base": 10, "color": "#dc2626"},
    "energy": {"base": 9, "color": "#ea580c"},
    "port": {"base": 8, "color": "#d97706"},
    "industry": {"base": 6, "color": "#65a30d"},
    "transport": {"base": 5, "color": "#0891b2"},
    "tourism": {"base": 4, "color": "#7c3aed"},
    "recreation": {"base": 3, "color": "#db2777"},
}

RISK_WEIGHTS = {
    "retreat_speed": 0.30,
    "current_distance": 0.25,
    "criticality": 0.25,
    "years_to_threshold": 0.20,
}

RISK_THRESHOLDS = {"low": (0, 33), "medium": (34, 66), "high": (67, 100)}
