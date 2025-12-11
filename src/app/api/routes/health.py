from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.security import AuthenticatedUser

router = APIRouter()


@router.get("/health", tags=["meta"])
async def healthcheck(
    _: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, str]:
    return {"status": "ok", "version": settings.app.version}
