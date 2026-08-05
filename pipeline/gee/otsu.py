"""Порог Оцу, посчитанный на стороне Earth Engine по гистограмме MNDWI.

Стандартный приём для GEE: клиентский Оцу (cv2/skimage) недоступен на
сервере, поэтому берём гистограмму через reduceRegion и максимизируем
межклассовую дисперсию вручную.
"""
import ee


def otsu_threshold(mndwi_image: ee.Image, region: ee.Geometry, scale: int, bins: int = 256) -> ee.Number:
    histogram = mndwi_image.reduceRegion(
        reducer=ee.Reducer.histogram(bins, None, None).combine(ee.Reducer.mean(), "", True).combine(ee.Reducer.variance(), "", True),
        geometry=region, scale=scale, maxPixels=1e10, bestEffort=True, tileScale=4,
    ).get("MNDWI_histogram")

    return ee.Number(_otsu_from_histogram(ee.Dictionary(histogram)))


def _otsu_from_histogram(histogram: ee.Dictionary) -> ee.Number:
    counts = ee.Array(ee.Dictionary(histogram).get("histogram"))
    means = ee.Array(ee.Dictionary(histogram).get("bucketMeans"))
    size = means.length().get([0])
    total = counts.reduce(ee.Reducer.sum(), [0]).get([0])
    sum_all = means.multiply(counts).reduce(ee.Reducer.sum(), [0]).get([0])

    indices = ee.List.sequence(1, size.subtract(1))

    def bcv_at(i):
        i = ee.Number(i)
        counts_a = counts.slice(0, 0, i)
        means_a = means.slice(0, 0, i)
        count_a = counts_a.reduce(ee.Reducer.sum(), [0]).get([0])
        mean_a = ee.Algorithms.If(
            ee.Number(count_a).gt(0),
            means_a.multiply(counts_a).reduce(ee.Reducer.sum(), [0]).get([0]),
            0,
        )
        mean_a = ee.Number(mean_a).divide(ee.Number(count_a).max(1))

        count_b = ee.Number(total).subtract(count_a)
        sum_b = ee.Number(sum_all).subtract(ee.Number(count_a).multiply(mean_a))
        mean_b = sum_b.divide(count_b.max(1))

        weight_a = ee.Number(count_a).divide(total)
        weight_b = ee.Number(count_b).divide(total)
        bcv = weight_a.multiply(weight_b).multiply(mean_a.subtract(mean_b).pow(2))
        return bcv

    bcvs = indices.map(bcv_at)
    max_bcv = ee.List(bcvs).reduce(ee.Reducer.max())
    best_index = ee.List(bcvs).indexOf(max_bcv)
    threshold = ee.Number(means.toList().get(ee.Number(best_index).add(1)))
    return threshold
