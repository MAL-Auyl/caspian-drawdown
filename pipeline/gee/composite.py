"""Медианный июльский композит по году с расширением окна при нехватке сцен."""
import ee

from pipeline.gee import config as cfg
from pipeline.gee.bands import collection_for_year
from pipeline.gee.indices import cloud_mask, scale_reflectance

CLOUD_PROP_BY_KIND = {"landsat": "CLOUD_COVER", "sentinel2": "CLOUDY_PIXEL_PERCENTAGE"}


def _filtered(coll_id: str, aoi: ee.Geometry, start: str, end: str, max_cloud: float):
    from pipeline.gee.bands import COLLECTIONS
    kind = COLLECTIONS[coll_id]["kind"]
    prop = CLOUD_PROP_BY_KIND[kind]
    return (
        ee.ImageCollection(coll_id)
        .filterBounds(aoi)
        .filterDate(start, end)
        .filter(ee.Filter.lte(prop, max_cloud))
    )


def build_year_composite(year: int, aoi: ee.Geometry):
    """Возвращает (composite, coll_id, scene_count, window) либо (None, coll_id, 0, window)."""
    coll_id = collection_for_year(year)
    windows = [
        (f"{year}-07-01", f"{year}-08-01"),
        (f"{year}-06-01", f"{year}-09-01"),  # расширение до июнь-август при нехватке сцен
    ]
    for start, end in windows:
        coll = _filtered(coll_id, aoi, start, end, cfg.MAX_CLOUD_PCT)
        n = coll.size().getInfo()
        if n > 0:
            scaled = coll.map(lambda img: cloud_mask(scale_reflectance(img, coll_id), coll_id))
            return scaled.median().clip(aoi), coll_id, n, (start, end)
    return None, coll_id, 0, windows[-1]
