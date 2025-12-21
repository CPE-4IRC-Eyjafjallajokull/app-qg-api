from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import IncidentPhase
from app.schemas.incidents import (
    IncidentPhaseCreate,
    IncidentPhaseRead,
    IncidentPhaseUpdate,
)

router = APIRouter(prefix="/phases")


@router.post("", response_model=IncidentPhaseRead, status_code=status.HTTP_201_CREATED)
async def create_incident_phase(
    payload: IncidentPhaseCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> IncidentPhase:
    phase = IncidentPhase(**payload.model_dump(exclude_unset=True))
    session.add(phase)
    await session.commit()
    await session.refresh(phase)
    return phase


@router.get("", response_model=list[IncidentPhaseRead])
async def list_incident_phases(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    incident_id: UUID | None = Query(None),
    phase_type_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[IncidentPhase]:
    stmt = select(IncidentPhase)
    if incident_id:
        stmt = stmt.where(IncidentPhase.incident_id == incident_id)
    if phase_type_id:
        stmt = stmt.where(IncidentPhase.phase_type_id == phase_type_id)
    stmt = stmt.order_by(IncidentPhase.priority).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{incident_phase_id}", response_model=IncidentPhaseRead)
async def get_incident_phase(
    incident_phase_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> IncidentPhase:
    return await fetch_one_or_404(
        session,
        select(IncidentPhase).where(
            IncidentPhase.incident_phase_id == incident_phase_id
        ),
        "Incident phase not found",
    )


@router.patch("/{incident_phase_id}", response_model=IncidentPhaseRead)
async def update_incident_phase(
    incident_phase_id: UUID,
    payload: IncidentPhaseUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> IncidentPhase:
    phase = await fetch_one_or_404(
        session,
        select(IncidentPhase).where(
            IncidentPhase.incident_phase_id == incident_phase_id
        ),
        "Incident phase not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(phase, field, value)
    await session.commit()
    await session.refresh(phase)
    return phase


@router.delete(
    "/{incident_phase_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_incident_phase(
    incident_phase_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    phase = await fetch_one_or_404(
        session,
        select(IncidentPhase).where(
            IncidentPhase.incident_phase_id == incident_phase_id
        ),
        "Incident phase not found",
    )
    await session.delete(phase)
    await session.commit()
