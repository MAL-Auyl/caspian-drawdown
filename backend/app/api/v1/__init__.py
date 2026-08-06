from fastapi import APIRouter

from . import routes_chat, routes_misc, routes_objects, routes_reports, routes_shorelines, routes_transects

router = APIRouter()
router.include_router(routes_misc.router)
router.include_router(routes_shorelines.router)
router.include_router(routes_transects.router)
router.include_router(routes_objects.router)
router.include_router(routes_reports.router)
router.include_router(routes_chat.router)
