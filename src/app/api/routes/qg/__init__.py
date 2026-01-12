from fastapi import APIRouter

from app.api.routes.qg.assignment_proposals import (
    router as assignment_proposals_router,
)
from app.api.routes.qg.incidents import router as incidents_router
from app.api.routes.qg.live import router as live_router
from app.api.routes.qg.vehicles import router as vehicles_router

router = APIRouter(prefix="/qg", tags=["qg"])

router.include_router(live_router)
router.include_router(incidents_router)
router.include_router(vehicles_router)
router.include_router(assignment_proposals_router)
