from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.events import router as events_router

router = APIRouter()

router.include_router(health_router)
router.include_router(events_router)
