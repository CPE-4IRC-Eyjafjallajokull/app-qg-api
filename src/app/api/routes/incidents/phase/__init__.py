from fastapi import APIRouter

from app.api.routes.incidents.phase.categories import router as phase_categories_router
from app.api.routes.incidents.phase.dependencies import (
    router as phase_dependencies_router,
)
from app.api.routes.incidents.phase.types import router as phase_types_router

router = APIRouter(tags=["incidents"], prefix="/phase")

router.include_router(phase_categories_router)
router.include_router(phase_types_router)
router.include_router(phase_dependencies_router)
