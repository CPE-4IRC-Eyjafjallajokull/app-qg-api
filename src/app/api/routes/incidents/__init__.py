from fastapi import APIRouter

from app.api.routes.incidents.incidents import router as incidents_router
from app.api.routes.incidents.phase_categories import router as phase_categories_router
from app.api.routes.incidents.phase_dependencies import (
    router as phase_dependencies_router,
)
from app.api.routes.incidents.phase_types import router as phase_types_router
from app.api.routes.incidents.phases import router as phases_router
from app.api.routes.incidents.queue import router as queue_router
from app.api.routes.incidents.vehicle_requirement_groups import (
    router as vehicle_requirement_groups_router,
)
from app.api.routes.incidents.vehicle_requirements import (
    router as vehicle_requirements_router,
)

router = APIRouter(tags=["incidents"])

router.include_router(queue_router)
router.include_router(incidents_router)
router.include_router(phase_categories_router)
router.include_router(phase_types_router)
router.include_router(phases_router)
router.include_router(phase_dependencies_router)
router.include_router(vehicle_requirement_groups_router)
router.include_router(vehicle_requirements_router)
