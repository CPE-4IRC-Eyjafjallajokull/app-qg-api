from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


async def fetch_one_or_404(session: AsyncSession, stmt, detail: str):
    """Execute a statement and raise 404 if no row is found."""
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return obj
