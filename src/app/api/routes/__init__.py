from fastapi import APIRouter, Depends

from app.api.dependencies import authorize_request
from app.api.routes.assignment_proposals import router as assignment_proposals_router
from app.api.routes.casualties import router as casualties_router
from app.api.routes.geo import router as geo_router
from app.api.routes.health import router as health_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.interest_points import router as interest_points_router
from app.api.routes.operators import router as operators_router
from app.api.routes.qg import router as qg_router
from app.api.routes.terrain import router as terrain_router
from app.api.routes.vehicles import router as vehicles_router

router = APIRouter()

router.include_router(geo_router, dependencies=[Depends(authorize_request)])
router.include_router(qg_router, dependencies=[Depends(authorize_request)])
router.include_router(terrain_router, dependencies=[Depends(authorize_request)])
router.include_router(incidents_router, dependencies=[Depends(authorize_request)])
router.include_router(
    assignment_proposals_router, dependencies=[Depends(authorize_request)]
)
router.include_router(operators_router, dependencies=[Depends(authorize_request)])
router.include_router(casualties_router, dependencies=[Depends(authorize_request)])
router.include_router(
    interest_points_router,
    dependencies=[Depends(authorize_request)],
)
router.include_router(vehicles_router, dependencies=[Depends(authorize_request)])
router.include_router(health_router)
