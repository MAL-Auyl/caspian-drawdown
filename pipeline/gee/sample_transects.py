"""Позиции трансект по MNDWI напрямую — без полигональной векторизации
всей береговой линии.

Смена подхода #1 (после первого теста): векторизация всего коридора в один
полигон даёт артефакты на изрезанном берегу и на границе самого коридора.

Смена подхода #2 (после второго теста): сэмплинг тысяч отдельных точечных
Feature с клиента — сам по себе узкое место (загрузка десятков тысяч
литеральных геометрий в запросе), а не вычисления на сервере. Правильный
способ — reduceRegions по геометриям ЛИНИЙ трансект: сервер сам растеризует
линию и отдаёт пиксели одним batch-запросом (539 трансект — 9 секунд,
а не то же самое точками — не укладывалось и в несколько минут).
Пиксели возвращаются без гарантии порядка вдоль линии, поэтому вместе с
MNDWI забираем координаты каждого пикселя (`ee.Image.pixelLonLat()`) и
сортируем на клиенте по проекции на трансекту.
"""
import ee
import pyproj
from shapely.geometry import LineString, Point
from shapely.ops import transform

from pipeline.gee import config as cfg

WORK_SCALE_FLOOR_M = 30

_TO_METRIC = pyproj.Transformer.from_crs(cfg.CRS_OUTPUT, cfg.CRS_METRIC, always_xy=True).transform
_TO_OUTPUT = pyproj.Transformer.from_crs(cfg.CRS_METRIC, cfg.CRS_OUTPUT, always_xy=True).transform


def _transects_to_fc(transects_metric: list[LineString]) -> ee.FeatureCollection:
    feats = []
    for i, t in enumerate(transects_metric):
        line_wgs84 = transform(_TO_OUTPUT, t)
        feats.append(ee.Feature(ee.Geometry.LineString(list(line_wgs84.coords)), {"transect_id": i}))
    return ee.FeatureCollection(feats)


def sample_mndwi_along_transects(mndwi_image: ee.Image, transects_metric: list[LineString], scale: int) -> dict[int, list[tuple[float, float]]]:
    """Возвращает {transect_id: [(distance_m_along_transect, mndwi_value), ...]}
    отсортированный по расстоянию от начала трансекты (суша) к концу (море)."""
    working = mndwi_image.select("MNDWI").addBands(ee.Image.pixelLonLat()).select(
        ["MNDWI", "longitude", "latitude"])
    fc = _transects_to_fc(transects_metric)
    sampled = working.reduceRegions(collection=fc, reducer=ee.Reducer.toList(3), scale=scale, tileScale=4).getInfo()

    result = {}
    for f, transect in zip(sampled["features"], transects_metric):
        t_id = f["properties"]["transect_id"]
        rows = f["properties"].get("list", [])
        dated = []
        for mndwi_val, lon, lat in rows:
            pt_metric = transform(_TO_METRIC, Point(lon, lat))
            d = transect.project(pt_metric)
            dated.append((d, mndwi_val))
        dated.sort(key=lambda x: x[0])
        result[t_id] = dated
    return result


def find_crossing(samples: list[tuple[float, float]], threshold: float) -> float | None:
    """Первое пересечение суша(<порог)->вода(>=порог) от начала луча (суша),
    с линейной интерполяцией между соседними пикселями вдоль линии."""
    prev = None
    for d, v in samples:
        if prev is not None and prev[1] < threshold <= v:
            span = v - prev[1]
            frac = (threshold - prev[1]) / span if span else 0.0
            return round(prev[0] + frac * (d - prev[0]), 1)
        prev = (d, v)
    return None
