from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import Reinforcement
from app.schemas.incidents import (
    ReinforcementCreate,
    ReinforcementRead,
    ReinforcementUpdate,
)

router = APIRouter(prefix="/reinforcements")


@router.post("", response_model=ReinforcementRead, status_code=status.HTTP_201_CREATED)
async def create_reinforcement(
    payload: ReinforcementCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> Reinforcement:
    reinforcement = Reinforcement(**payload.model_dump(exclude_unset=True))
    session.add(reinforcement)
    await session.commit()
    await session.refresh(reinforcement)
    return reinforcement


@router.get("", response_model=list[ReinforcementRead])
async def list_reinforcements(
    limit: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
    incident_phase_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[Reinforcement]:
    stmt = select(Reinforcement)
    if incident_phase_id:
        stmt = stmt.where(Reinforcement.incident_phase_id == incident_phase_id)
    stmt = stmt.order_by(Reinforcement.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{reinforcement_id}", response_model=ReinforcementRead)
async def get_reinforcement(
    reinforcement_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
) -> Reinforcement:
    return await fetch_one_or_404(
        session,
        select(Reinforcement).where(Reinforcement.reinforcement_id == reinforcement_id),
        "Reinforcement not found",
    )


@router.patch("/{reinforcement_id}", response_model=ReinforcementRead)
async def update_reinforcement(
    reinforcement_id: UUID,
    payload: ReinforcementUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> Reinforcement:
    reinforcement = await fetch_one_or_404(
        session,
        select(Reinforcement).where(Reinforcement.reinforcement_id == reinforcement_id),
        "Reinforcement not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(reinforcement, field, value)
    await session.commit()
    await session.refresh(reinforcement)
    return reinforcement


@router.delete(
    "/{reinforcement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_reinforcement(
    reinforcement_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
) -> None:
    reinforcement = await fetch_one_or_404(
        session,
        select(Reinforcement).where(Reinforcement.reinforcement_id == reinforcement_id),
        "Reinforcement not found",
    )
    await session.delete(reinforcement)
    await session.commit()
