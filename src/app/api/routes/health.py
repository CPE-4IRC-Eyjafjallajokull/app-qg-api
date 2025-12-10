from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health", tags=["meta"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "version": settings.version}
