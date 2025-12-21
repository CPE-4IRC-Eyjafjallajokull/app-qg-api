from fastapi import APIRouter

from app.api.routes.interventions.interventions import router as interventions_router

router = APIRouter(tags=["interventions"])

router.include_router(interventions_router)
