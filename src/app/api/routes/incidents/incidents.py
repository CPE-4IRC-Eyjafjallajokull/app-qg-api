from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import Incident
from app.schemas.incidents import IncidentCreate, IncidentRead, IncidentUpdate

router = APIRouter()


@router.post("/", response_model=IncidentRead, status_code=status.HTTP_201_CREATED)
async def create_incident(
    payload: IncidentCreate, session: AsyncSession = Depends(get_postgres_session)
) -> Incident:
    incident = Incident(**payload.model_dump(exclude_unset=True))
    session.add(incident)
    await session.commit()
    await session.refresh(incident)
    return incident


@router.get("/", response_model=list[IncidentRead])
async def list_incidents(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    created_by_operator_id: UUID | None = Query(None),
    city: str | None = Query(None),
    zipcode: str | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[Incident]:
    stmt = select(Incident)
    if created_by_operator_id:
        stmt = stmt.where(Incident.created_by_operator_id == created_by_operator_id)
    if city:
        stmt = stmt.where(Incident.city == city)
    if zipcode:
        stmt = stmt.where(Incident.zipcode == str(zipcode))
    stmt = stmt.order_by(Incident.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{incident_id}", response_model=IncidentRead)
async def get_incident(
    incident_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> Incident:
    return await fetch_one_or_404(
        session,
        select(Incident).where(Incident.incident_id == incident_id),
        "Incident not found",
    )


@router.patch("/{incident_id}", response_model=IncidentRead)
async def update_incident(
    incident_id: UUID,
    payload: IncidentUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> Incident:
    incident = await fetch_one_or_404(
        session,
        select(Incident).where(Incident.incident_id == incident_id),
        "Incident not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(incident, field, value)
    await session.commit()
    await session.refresh(incident)
    return incident


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_incident(
    incident_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    incident = await fetch_one_or_404(
        session,
        select(Incident).where(Incident.incident_id == incident_id),
        "Incident not found",
    )
    await session.delete(incident)
    await session.commit()
