from fastapi import APIRouter

from app.api.routes.vehicles.assignments import router as assignments_router
from app.api.routes.vehicles.consumables import router as consumable_types_router
from app.api.routes.vehicles.energies import router as energies_router
from app.api.routes.vehicles.position_logs import router as position_logs_router
from app.api.routes.vehicles.types import router as types_router
from app.api.routes.vehicles.vehicle_statuses import router as vehicle_statuses_router
from app.api.routes.vehicles.vehicles import router as vehicles_router

router = APIRouter(tags=["vehicles"])

router.include_router(energies_router)
router.include_router(types_router)
router.include_router(vehicle_statuses_router)
router.include_router(consumable_types_router)
router.include_router(assignments_router)
router.include_router(position_logs_router)
router.include_router(vehicles_router)
