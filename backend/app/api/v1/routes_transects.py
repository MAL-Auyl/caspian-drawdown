from fastapi import APIRouter, HTTPException, Query

from app.services.store import store

router = APIRouter()


@router.get("/transects")
def list_transects(
    confidence: str | None = Query(default=None),
    min_speed: float | None = Query(default=None),
    max_speed: float | None = Query(default=None),
):
    feats = store.transects["features"]
    if confidence:
        feats = [f for f in feats if f["properties"]["confidence"] == confidence]
    if min_speed is not None:
        feats = [f for f in feats if f["properties"]["speed_m_per_year"] >= min_speed]
    if max_speed is not None:
        feats = [f for f in feats if f["properties"]["speed_m_per_year"] <= max_speed]
    return {"count": len(feats), "geojson": {"type": "FeatureCollection", "features": feats}}


@router.get("/transects/{transect_id}")
def get_transect(transect_id: int):
    f = store.transect_by_id(transect_id)
    if not f:
        raise HTTPException(status_code=404, detail={
            "detail": f"Нет сегмента с id={transect_id}", "code": "TRANSECT_NOT_FOUND",
        })
    props = f["properties"]
    nearest_objects = []
    if store.objects:
        for obj in store.objects["features"]:
            if obj["properties"]["nearest_transect_id"] == transect_id:
                nearest_objects.append({
                    "object_id": obj["properties"]["object_id"],
                    "name_ru": obj["properties"]["name_ru"],
                })
    return {
        "transect_id": transect_id,
        "positions": props["positions"],
        "regression": {
            "model": "linear",
            "slope_m_per_year": props["speed_m_per_year"],
            "r_squared": props["r_squared"],
            "std_error": props["std_error"],
            "confidence_interval_95": [props["ci_95_low"], props["ci_95_high"]],
        },
        "total_retreat_m": props["total_retreat_m"],
        "confidence": props["confidence"],
        "nearest_objects": nearest_objects,
    }
