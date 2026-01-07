from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import CasualtyStatus
from app.schemas.casualties import (
    CasualtyStatusCreate,
    CasualtyStatusRead,
    CasualtyStatusUpdate,
)

router = APIRouter(prefix="/statuses")


@router.post("", response_model=CasualtyStatusRead, status_code=status.HTTP_201_CREATED)
async def create_casualty_status(
    payload: CasualtyStatusCreate, session: AsyncSession = Depends(get_postgres_session)
) -> CasualtyStatus:
    casualty_status = CasualtyStatus(**payload.model_dump(exclude_unset=True))
    session.add(casualty_status)
    await session.commit()
    await session.refresh(casualty_status)
    return casualty_status


@router.get("", response_model=list[CasualtyStatusRead])
async def list_casualty_statuses(
    limit: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[CasualtyStatus]:
    stmt = (
        select(CasualtyStatus)
        .order_by(CasualtyStatus.label)
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{casualty_status_id}", response_model=CasualtyStatusRead)
async def get_casualty_status(
    casualty_status_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> CasualtyStatus:
    return await fetch_one_or_404(
        session,
        select(CasualtyStatus).where(
            CasualtyStatus.casualty_status_id == casualty_status_id
        ),
        "Casualty status not found",
    )


@router.patch("/{casualty_status_id}", response_model=CasualtyStatusRead)
async def update_casualty_status(
    casualty_status_id: UUID,
    payload: CasualtyStatusUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> CasualtyStatus:
    casualty_status = await fetch_one_or_404(
        session,
        select(CasualtyStatus).where(
            CasualtyStatus.casualty_status_id == casualty_status_id
        ),
        "Casualty status not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(casualty_status, field, value)
    await session.commit()
    await session.refresh(casualty_status)
    return casualty_status


@router.delete(
    "/{casualty_status_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_casualty_status(
    casualty_status_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    casualty_status = await fetch_one_or_404(
        session,
        select(CasualtyStatus).where(
            CasualtyStatus.casualty_status_id == casualty_status_id
        ),
        "Casualty status not found",
    )
    await session.delete(casualty_status)
    await session.commit()
