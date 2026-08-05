from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.services import reports_db
from app.services.store import store

router = APIRouter()

AOI_LON = (50.20, 52.90)
AOI_LAT = (42.55, 45.40)


class ReportIn(BaseModel):
    latitude: float
    longitude: float
    category: str
    description: str = Field(min_length=10, max_length=1000)
    contact: str | None = None

    @field_validator("category")
    @classmethod
    def category_valid(cls, v):
        if v not in reports_db.CATEGORIES:
            raise ValueError("invalid category")
        return v


@router.post("/reports", status_code=201)
def create_report(payload: ReportIn, request: Request):
    if not (AOI_LON[0] <= payload.longitude <= AOI_LON[1] and AOI_LAT[0] <= payload.latitude <= AOI_LAT[1]):
        raise HTTPException(status_code=400, detail={
            "detail": "Координаты вне региона Мангистау", "code": "OUT_OF_AOI",
        })

    client_ip = request.client.host if request.client else "unknown"
    if reports_db.rate_limited(client_ip):
        raise HTTPException(status_code=429, detail={
            "detail": "Превышен лимит сообщений — не более 5 в час", "code": "RATE_LIMITED",
        })

    nearest = store.nearest_transect(payload.longitude, payload.latitude)
    nearest_id = nearest["properties"]["transect_id"] if nearest else None

    report_id, created_at = reports_db.insert_report(
        payload.latitude, payload.longitude, payload.category,
        payload.description, payload.contact, nearest_id, client_ip,
    )
    return {
        "report_id": report_id,
        "status": "received",
        "created_at": created_at,
        "nearest_transect_id": nearest_id,
    }


@router.get("/reports")
def list_reports():
    return {"reports": reports_db.list_reports()}
