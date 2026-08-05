"""MNDWI и облачные/качественные маски по типу коллекции."""
import ee

from pipeline.gee.bands import COLLECTIONS, LANDSAT_SR_OFFSET, LANDSAT_SR_SCALE, S2_SR_SCALE


def scale_reflectance(image: ee.Image, coll_id: str) -> ee.Image:
    kind = COLLECTIONS[coll_id]["kind"]
    if kind == "landsat":
        optical = image.select("SR_B.").multiply(LANDSAT_SR_SCALE).add(LANDSAT_SR_OFFSET)
        return image.addBands(optical, overwrite=True)
    optical = image.select(["B.*"]).multiply(S2_SR_SCALE)
    return image.addBands(optical, overwrite=True)


def cloud_mask(image: ee.Image, coll_id: str) -> ee.Image:
    kind = COLLECTIONS[coll_id]["kind"]
    if kind == "landsat":
        qa = image.select("QA_PIXEL")
        cloud = 1 << 3
        cloud_shadow = 1 << 4
        dilated_cloud = 1 << 1
        mask = (
            qa.bitwiseAnd(cloud).eq(0)
            .And(qa.bitwiseAnd(cloud_shadow).eq(0))
            .And(qa.bitwiseAnd(dilated_cloud).eq(0))
        )
        return image.updateMask(mask)

    scl = image.select("SCL")
    # 3=shadow, 8/9=cloud medium/high, 10=cirrus, 11=snow
    mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11))
    return image.updateMask(mask)


def mndwi(image: ee.Image, coll_id: str) -> ee.Image:
    b = COLLECTIONS[coll_id]
    return image.normalizedDifference([b["green"], b["swir"]]).rename("MNDWI")
