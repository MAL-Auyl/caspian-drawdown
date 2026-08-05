from fastapi import APIRouter, HTTPException, Query

from app.services.store import store

router = APIRouter()


@router.get("/objects")
def list_objects():
    fc = store.objects
    return {"count": len(fc["features"]), "geojson": fc}


def _get_or_404(object_id: int):
    obj = store.object_by_id(object_id)
    if not obj:
        raise HTTPException(status_code=404, detail={
            "detail": f"Нет объекта с id={object_id}", "code": "OBJECT_NOT_FOUND",
        })
    return obj


@router.get("/objects/{object_id}")
def get_object(object_id: int):
    obj = _get_or_404(object_id)
    p = obj["properties"]
    return {
        "object_id": p["object_id"],
        "name": {"ru": p["name_ru"], "kk": p["name_kk"], "en": p["name_en"]},
        "category": p["category"],
        "criticality": p["criticality"],
        "geometry": obj["geometry"],
        "shoreline_distance": {
            "2000_m": p["distance_to_shore_2000_m"],
            "2010_m": p["distance_to_shore_2010_m"],
            "2020_m": p["distance_to_shore_2020_m"],
            "2026_m": p["distance_to_shore_2026_m"],
            "change_m": round(p["distance_to_shore_2026_m"] - p["distance_to_shore_2000_m"], 1),
            "change_pct": round(
                (p["distance_to_shore_2026_m"] - p["distance_to_shore_2000_m"])
                / p["distance_to_shore_2000_m"] * 100, 1,
            ) if p["distance_to_shore_2000_m"] else None,
        },
        "nearest_transect_id": p["nearest_transect_id"],
        "speed_m_per_year": p["speed_m_per_year"],
        "risk": {"score": p["risk_score"], "level": p["risk_level"]},
        "forecast": {
            "2030_m": p["forecast"]["baseline"]["2030"],
            "2035_m": p["forecast"]["baseline"]["2035"],
            "2040_m": p["forecast"]["baseline"]["2040"],
            "model": "linear",
        },
        "description": {"ru": p["description_ru"], "kk": p["description_kk"], "en": p["description_en"]},
        "recommendation": {"ru": p["recommendation_ru"], "en": p["recommendation_en"]},
        "uncertainty_note": {
            "ru": "Погрешность метода — по контрольным участкам. Расстояния — от уреза воды по спутниковому снимку июля.",
        },
    }


@router.get("/objects/{object_id}/risk")
def get_object_risk(object_id: int):
    obj = _get_or_404(object_id)
    p = obj["properties"]
    comps = p["risk_components"]
    components = [
        {"name": "retreat_speed", "raw": comps["speed"]["raw"], "unit": "м/год",
         "normalized": comps["speed"]["normalized"], "weight": comps["speed"]["weight"],
         "contribution": round(comps["speed"]["normalized"] * comps["speed"]["weight"], 1)},
        {"name": "current_distance", "raw": comps["distance"]["raw"], "unit": "м",
         "normalized": comps["distance"]["normalized"], "weight": comps["distance"]["weight"],
         "contribution": round(comps["distance"]["normalized"] * comps["distance"]["weight"], 1)},
        {"name": "criticality", "raw": comps["criticality"]["raw"], "unit": "1–10",
         "normalized": comps["criticality"]["normalized"], "weight": comps["criticality"]["weight"],
         "contribution": round(comps["criticality"]["normalized"] * comps["criticality"]["weight"], 1)},
        {"name": "years_to_threshold", "raw": comps["years_to_threshold"]["raw"], "unit": "лет",
         "normalized": comps["years_to_threshold"]["normalized"], "weight": comps["years_to_threshold"]["weight"],
         "contribution": round(comps["years_to_threshold"]["normalized"] * comps["years_to_threshold"]["weight"], 1)},
    ]
    return {
        "object_id": object_id,
        "score": p["risk_score"],
        "level": p["risk_level"],
        "components": components,
        "formula": "score = Σ(normalized_i × weight_i)",
        "thresholds": {"low": "0–33", "medium": "34–66", "high": "67–100"},
    }


@router.get("/objects/{object_id}/forecast")
def get_object_forecast(object_id: int, horizons: str = Query(default="2030,2035,2040")):
    obj = _get_or_404(object_id)
    p = obj["properties"]
    return {
        "object_id": object_id,
        "current_distance_m": p["distance_to_shore_2026_m"],
        "scenarios": {
            "optimistic": {**p["forecast"]["optimistic"], "basis": "нижняя граница диапазона", "assumption": "темп замедляется"},
            "baseline": {**p["forecast"]["baseline"], "basis": "линейная регрессия", "assumption": "текущий тренд сохраняется"},
            "pessimistic": {**p["forecast"]["pessimistic"], "basis": "полиномиальная регрессия 2-й степени", "assumption": "темп ускоряется"},
        },
        "model_quality": {"r_squared": None, "valid_observations": None, "std_error": None},
        "disclaimer": {
            "ru": "Сценарная экстраполяция наблюдаемого тренда, а не гидродинамический прогноз. "
                  "Не учитывает изменения стока Волги и Урала, климатические сценарии и инженерные мероприятия.",
        },
    }
