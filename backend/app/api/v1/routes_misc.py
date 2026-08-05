from fastapi import APIRouter

from app.services.store import store

router = APIRouter()


@router.get("/statistics")
def get_statistics():
    return store.stats


@router.get("/dust")
def get_dust():
    return {
        "model": "indicative_wind_transport",
        "wind_rose_source": "Open-Meteo Archive, 2000–2026",
        "threshold_wind_ms": 8.0,
        "geojson": store.dust,
        "disclaimer": {
            "ru": "Индикативная модель ветрового переноса. Не заменяет моделирование качества атмосферного воздуха.",
        },
    }


@router.get("/exposed-seabed")
def get_exposed_seabed():
    return store.seabed


@router.get("/meta")
def get_meta():
    return store.meta


@router.get("/health")
def health():
    return {"status": "ok", "data_loaded": store.is_loaded, "years": len(store.shorelines)}


@router.get("/bootstrap")
def bootstrap():
    meta = dict(store.meta or {})
    meta.update({
        "years": [y for y in range(2000, 2027)],
        "missing_years": [2012],
    })
    return {
        "meta": meta,
        "shorelines": {str(y): fc for y, fc in store.shorelines.items()},
        "transects": store.transects,
        "objects": store.objects,
        "dust_zones": store.dust,
        "exposed_seabed": store.seabed,
        "statistics": store.stats,
    }
