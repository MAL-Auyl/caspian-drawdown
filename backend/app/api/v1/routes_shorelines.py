from fastapi import APIRouter, HTTPException, Query

from app.services.store import store

router = APIRouter()


def _year_meta(year: int):
    fc = store.shorelines.get(year)
    if not fc:
        return None
    props = fc["features"][0]["properties"]
    return {"year": year, **{k: v for k, v in props.items() if k != "year"}}


@router.get("/shorelines")
def list_shorelines():
    years = store.available_years()
    span = range(min(years, default=2000), max(years, default=2000) + 1)
    years_meta = []
    for y in span:
        meta = _year_meta(y)
        years_meta.append(meta or {
            "year": y, "sensor": None, "data_quality": "missing",
            "note": "Данные за этот год отсутствуют",
        })
    return {"years": years_meta, "count": len(years)}


@router.get("/shorelines/{year}")
def get_shoreline(year: int, simplify: bool = True, bbox: str | None = Query(default=None)):
    fc = store.shorelines.get(year)
    if not fc:
        raise HTTPException(status_code=404, detail={
            "detail": f"Данные за {year} год отсутствуют",
            "code": "YEAR_NOT_AVAILABLE",
            "available_years": store.available_years(),
        })
    return {"year": year, "data_quality": fc["features"][0]["properties"].get("data_quality", "good"), "geojson": fc}
