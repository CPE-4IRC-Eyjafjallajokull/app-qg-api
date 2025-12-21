from fastapi import APIRouter

from app.api.routes.operators.operators import router as operators_router

router = APIRouter(tags=["operators"])

router.include_router(operators_router)
