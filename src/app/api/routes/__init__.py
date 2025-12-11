from fastapi import APIRouter

from app.api.routes.events import router as events_router
from app.api.routes.health import router as health_router
from app.api.routes.incidents import router as incidents_router

router = APIRouter()

router.include_router(health_router)
router.include_router(events_router)
router.include_router(incidents_router)
