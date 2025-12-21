from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import IncidentPhaseDependency
from app.models.enums import IncidentPhaseDependencyKind
from app.schemas.incidents import (
    IncidentPhaseDependencyCreate,
    IncidentPhaseDependencyRead,
    IncidentPhaseDependencyUpdate,
)

router = APIRouter(prefix="/dependencies")


@router.post(
    "",
    response_model=IncidentPhaseDependencyRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_incident_phase_dependency(
    payload: IncidentPhaseDependencyCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> IncidentPhaseDependency:
    dependency = IncidentPhaseDependency(**payload.model_dump(exclude_unset=True))
    session.add(dependency)
    await session.commit()
    await session.refresh(dependency)
    return dependency


@router.get("", response_model=list[IncidentPhaseDependencyRead])
async def list_incident_phase_dependencies(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    incident_phase_id: UUID | None = Query(None),
    depends_on_incident_phase_id: UUID | None = Query(None),
    kind: IncidentPhaseDependencyKind | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[IncidentPhaseDependency]:
    stmt = select(IncidentPhaseDependency)
    if incident_phase_id:
        stmt = stmt.where(
            IncidentPhaseDependency.incident_phase_id == incident_phase_id
        )
    if depends_on_incident_phase_id:
        stmt = stmt.where(
            IncidentPhaseDependency.depends_on_incident_phase_id
            == depends_on_incident_phase_id
        )
    if kind:
        stmt = stmt.where(IncidentPhaseDependency.kind == kind)
    stmt = stmt.order_by(IncidentPhaseDependency.created_at.desc())
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{dependency_id}", response_model=IncidentPhaseDependencyRead)
async def get_incident_phase_dependency(
    dependency_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> IncidentPhaseDependency:
    return await fetch_one_or_404(
        session,
        select(IncidentPhaseDependency).where(
            IncidentPhaseDependency.id == dependency_id
        ),
        "Incident phase dependency not found",
    )


@router.patch("/{dependency_id}", response_model=IncidentPhaseDependencyRead)
async def update_incident_phase_dependency(
    dependency_id: UUID,
    payload: IncidentPhaseDependencyUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> IncidentPhaseDependency:
    dependency = await fetch_one_or_404(
        session,
        select(IncidentPhaseDependency).where(
            IncidentPhaseDependency.id == dependency_id
        ),
        "Incident phase dependency not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(dependency, field, value)
    await session.commit()
    await session.refresh(dependency)
    return dependency


@router.delete(
    "/{dependency_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_incident_phase_dependency(
    dependency_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    dependency = await fetch_one_or_404(
        session,
        select(IncidentPhaseDependency).where(
            IncidentPhaseDependency.id == dependency_id
        ),
        "Incident phase dependency not found",
    )
    await session.delete(dependency)
    await session.commit()
