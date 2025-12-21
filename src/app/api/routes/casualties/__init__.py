from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.casualties.statuses import router as statuses_router
from app.api.routes.casualties.transports import router as transports_router
from app.api.routes.casualties.types import router as types_router
from app.api.routes.utils import fetch_one_or_404
from app.models import Casualty
from app.schemas.casualties import CasualtyCreate, CasualtyRead, CasualtyUpdate

router = APIRouter(tags=["casualties"], prefix="/casualties")

router.include_router(types_router)
router.include_router(statuses_router)
router.include_router(transports_router)


@router.post("", response_model=CasualtyRead, status_code=status.HTTP_201_CREATED)
async def create_casualty(
    payload: CasualtyCreate, session: AsyncSession = Depends(get_postgres_session)
) -> Casualty:
    casualty = Casualty(**payload.model_dump(exclude_unset=True))
    session.add(casualty)
    await session.commit()
    await session.refresh(casualty)
    return casualty


@router.get("", response_model=list[CasualtyRead])
async def list_casualties(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    incident_phase_id: UUID | None = Query(None),
    casualty_type_id: UUID | None = Query(None),
    casualty_status_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[Casualty]:
    stmt = select(Casualty)
    if incident_phase_id:
        stmt = stmt.where(Casualty.incident_phase_id == incident_phase_id)
    if casualty_type_id:
        stmt = stmt.where(Casualty.casualty_type_id == casualty_type_id)
    if casualty_status_id:
        stmt = stmt.where(Casualty.casualty_status_id == casualty_status_id)
    stmt = stmt.order_by(Casualty.reported_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{casualty_id}", response_model=CasualtyRead)
async def get_casualty(
    casualty_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> Casualty:
    return await fetch_one_or_404(
        session,
        select(Casualty).where(Casualty.casualty_id == casualty_id),
        "Casualty not found",
    )


@router.patch("/{casualty_id}", response_model=CasualtyRead)
async def update_casualty(
    casualty_id: UUID,
    payload: CasualtyUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> Casualty:
    casualty = await fetch_one_or_404(
        session,
        select(Casualty).where(Casualty.casualty_id == casualty_id),
        "Casualty not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(casualty, field, value)
    await session.commit()
    await session.refresh(casualty)
    return casualty


@router.delete(
    "/{casualty_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_casualty(
    casualty_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    casualty = await fetch_one_or_404(
        session,
        select(Casualty).where(Casualty.casualty_id == casualty_id),
        "Casualty not found",
    )
    await session.delete(casualty)
    await session.commit()
