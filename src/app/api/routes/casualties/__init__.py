from fastapi import APIRouter

from app.api.routes.casualties.casualties import router as casualties_router
from app.api.routes.casualties.statuses import router as statuses_router
from app.api.routes.casualties.transports import router as transports_router
from app.api.routes.casualties.types import router as types_router

router = APIRouter(tags=["casualties"])

router.include_router(types_router)
router.include_router(statuses_router)
router.include_router(transports_router)
router.include_router(casualties_router)
