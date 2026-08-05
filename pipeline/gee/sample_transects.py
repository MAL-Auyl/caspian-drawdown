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
from pipeline.gee.bands import NIR_WATER_MAX

WORK_SCALE_FLOOR_M = 30

_TO_METRIC = pyproj.Transformer.from_crs(cfg.CRS_OUTPUT, cfg.CRS_METRIC, always_xy=True).transform
_TO_OUTPUT = pyproj.Transformer.from_crs(cfg.CRS_METRIC, cfg.CRS_OUTPUT, always_xy=True).transform


def _transects_to_fc(transects_metric: list[LineString]) -> ee.FeatureCollection:
    feats = []
    for i, t in enumerate(transects_metric):
        line_wgs84 = transform(_TO_OUTPUT, t)
        feats.append(ee.Feature(ee.Geometry.LineString(list(line_wgs84.coords)), {"transect_id": i}))
    return ee.FeatureCollection(feats)


def sample_mndwi_along_transects(index_image: ee.Image, transects_metric: list[LineString], scale: int) -> dict[int, list[tuple[float, float, float]]]:
    """Возвращает {transect_id: [(distance_m_along_transect, mndwi_value, nir_value), ...]}
    отсортированный по расстоянию от начала трансекты (суша) к концу (море).
    index_image — двухканальный (MNDWI, NIR), см. indices.mndwi_with_nir."""
    working = index_image.select(["MNDWI", "NIR"]).addBands(ee.Image.pixelLonLat()).select(
        ["MNDWI", "NIR", "longitude", "latitude"])
    fc = _transects_to_fc(transects_metric)
    sampled = working.reduceRegions(collection=fc, reducer=ee.Reducer.toList(4), scale=scale, tileScale=4).getInfo()

    result = {}
    for f, transect in zip(sampled["features"], transects_metric):
        t_id = f["properties"]["transect_id"]
        rows = f["properties"].get("list", [])
        dated = []
        for mndwi_val, nir_val, lon, lat in rows:
            pt_metric = transform(_TO_METRIC, Point(lon, lat))
            d = transect.project(pt_metric)
            dated.append((d, mndwi_val, nir_val))
        dated.sort(key=lambda x: x[0])
        result[t_id] = dated
    return result


def find_crossing(samples: list[tuple[float, float, float]], threshold: float, nir_max: float = NIR_WATER_MAX) -> float | None:
    """Первое пересечение суша(<порог)->вода(>=порог, NIR<nir_max) от начала
    луча (суша), с линейной интерполяцией между соседними пикселями.

    Требуем оба условия (MNDWI выше порога Оцу И низкий NIR) — городские
    поверхности (асфальт, тени, промзона) могут ошибочно проходить порог
    Оцу по одному MNDWI, но остаются яркими в NIR."""
    prev = None
    for d, v, nir in samples:
        is_water = v >= threshold and nir < nir_max
        if prev is not None and not prev[2] and is_water:
            span = v - prev[1]
            frac = (threshold - prev[1]) / span if span else 0.0
            return round(prev[0] + frac * (d - prev[0]), 1)
        prev = (d, v, is_water)
    return None
