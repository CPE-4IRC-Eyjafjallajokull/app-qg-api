from fastapi import APIRouter

from app.api.routes.interest_points.consumable_types import (
    router as consumable_types_router,
)
from app.api.routes.interest_points.consumables import router as consumables_router
from app.api.routes.interest_points.interest_points import (
    router as interest_points_router,
)
from app.api.routes.interest_points.kinds import router as kinds_router

router = APIRouter(tags=["interest-points"])

router.include_router(kinds_router)
router.include_router(consumable_types_router)
router.include_router(consumables_router)
router.include_router(interest_points_router)
