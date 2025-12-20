from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.vehicles.utils import fetch_one_or_404
from app.models import VehicleAssignment
from app.schemas.vehicles import (
    VehicleAssignmentCreate,
    VehicleAssignmentRead,
    VehicleAssignmentUpdate,
)

router = APIRouter()


@router.post(
    "/assignments",
    response_model=VehicleAssignmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_vehicle_assignment(
    payload: VehicleAssignmentCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleAssignment:
    assignment = VehicleAssignment(**payload.model_dump(exclude_unset=True))
    session.add(assignment)
    await session.commit()
    await session.refresh(assignment)
    return assignment


@router.get("/assignments", response_model=list[VehicleAssignmentRead])
async def list_vehicle_assignments(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    vehicle_id: UUID | None = Query(None),
    intervention_id: UUID | None = Query(None),
    active_only: bool = Query(
        False, description="If true, only return assignments without unassigned_at"
    ),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[VehicleAssignment]:
    stmt = select(VehicleAssignment)
    if vehicle_id:
        stmt = stmt.where(VehicleAssignment.vehicle_id == vehicle_id)
    if intervention_id:
        stmt = stmt.where(VehicleAssignment.intervention_id == intervention_id)
    if active_only:
        stmt = stmt.where(VehicleAssignment.unassigned_at.is_(None))
    stmt = (
        stmt.order_by(VehicleAssignment.assigned_at.desc()).offset(offset).limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get(
    "/assignments/{vehicle_assignment_id}",
    response_model=VehicleAssignmentRead,
)
async def get_vehicle_assignment(
    vehicle_assignment_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> VehicleAssignment:
    return await fetch_one_or_404(
        session,
        select(VehicleAssignment).where(
            VehicleAssignment.vehicle_assignment_id == vehicle_assignment_id
        ),
        "Vehicle assignment not found",
    )


@router.patch(
    "/assignments/{vehicle_assignment_id}",
    response_model=VehicleAssignmentRead,
)
async def update_vehicle_assignment(
    vehicle_assignment_id: UUID,
    payload: VehicleAssignmentUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleAssignment:
    assignment = await fetch_one_or_404(
        session,
        select(VehicleAssignment).where(
            VehicleAssignment.vehicle_assignment_id == vehicle_assignment_id
        ),
        "Vehicle assignment not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(assignment, field, value)
    await session.commit()
    await session.refresh(assignment)
    return assignment


@router.delete(
    "/assignments/{vehicle_assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_vehicle_assignment(
    vehicle_assignment_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    assignment = await fetch_one_or_404(
        session,
        select(VehicleAssignment).where(
            VehicleAssignment.vehicle_assignment_id == vehicle_assignment_id
        ),
        "Vehicle assignment not found",
    )
    await session.delete(assignment)
    await session.commit()
