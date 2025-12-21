from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import Intervention
from app.schemas.interventions import (
    InterventionCreate,
    InterventionRead,
    InterventionUpdate,
)

router = APIRouter()


@router.post("/", response_model=InterventionRead, status_code=status.HTTP_201_CREATED)
async def create_intervention(
    payload: InterventionCreate, session: AsyncSession = Depends(get_postgres_session)
) -> Intervention:
    intervention = Intervention(**payload.model_dump(exclude_unset=True))
    session.add(intervention)
    await session.commit()
    await session.refresh(intervention)
    return intervention


@router.get("/", response_model=list[InterventionRead])
async def list_interventions(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    incident_id: UUID | None = Query(None),
    created_by_operator_id: UUID | None = Query(None),
    validated_by_operator_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[Intervention]:
    stmt = select(Intervention)
    if incident_id:
        stmt = stmt.where(Intervention.incident_id == incident_id)
    if created_by_operator_id:
        stmt = stmt.where(Intervention.created_by_operator_id == created_by_operator_id)
    if validated_by_operator_id:
        stmt = stmt.where(
            Intervention.validated_by_operator_id == validated_by_operator_id
        )
    stmt = stmt.order_by(Intervention.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{intervention_id}", response_model=InterventionRead)
async def get_intervention(
    intervention_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> Intervention:
    return await fetch_one_or_404(
        session,
        select(Intervention).where(Intervention.intervention_id == intervention_id),
        "Intervention not found",
    )


@router.patch("/{intervention_id}", response_model=InterventionRead)
async def update_intervention(
    intervention_id: UUID,
    payload: InterventionUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> Intervention:
    intervention = await fetch_one_or_404(
        session,
        select(Intervention).where(Intervention.intervention_id == intervention_id),
        "Intervention not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(intervention, field, value)
    await session.commit()
    await session.refresh(intervention)
    return intervention


@router.delete(
    "/{intervention_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_intervention(
    intervention_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    intervention = await fetch_one_or_404(
        session,
        select(Intervention).where(Intervention.intervention_id == intervention_id),
        "Intervention not found",
    )
    await session.delete(intervention)
    await session.commit()
