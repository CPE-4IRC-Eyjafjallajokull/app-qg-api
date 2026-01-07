from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health", tags=["api"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "version": settings.app.version}
