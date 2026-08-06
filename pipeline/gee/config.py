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
# 2003-2005: Landsat 7 SLC-off (с мая 2003) + недостаточно чистых сцен Landsat 5
# для AOI в эти годы — пайплайн не смог собрать композит.
# 2012: Landsat 5 закрыт, Landsat 8 ещё не запущен.
MISSING_YEARS = [2003, 2004, 2005, 2012]
MONTH = 7                   # только июль — минимум сгонно-нагонных искажений
MAX_CLOUD_PCT = 10
MAX_WIND_MS = 8.0

# Грубая осевая линия побережья Мангистау (Баутино -> Актау -> юг к границе),
# используется только чтобы ОГРАНИЧИТЬ область тяжёлых вычислений (Оцу,
# векторизация) прибрежным коридором вместо всего прямоугольника AOI —
# считать Оцу и векторизовать открытое море в 100 км от берега не нужно и
# на порядок дороже. Точность самой береговой линии от этого не зависит:
# она находится по пикселям MNDWI внутри коридора.
COAST_WAYPOINTS = [
    (50.28, 44.56),  # Баутино / Тюб-Караган
    (50.55, 44.30),
    (50.85, 44.05),
    (51.05, 43.85),
    (51.15, 43.70),
    (51.20, 43.64),  # Актау
    (51.45, 43.30),  # Курык
    (51.85, 42.95),
    (52.30, 42.65),
]
COASTAL_CORRIDOR_HALF_WIDTH_M = 9000

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
