from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import PhaseTypeVehicleRequirement
from app.schemas.incidents import (
    PhaseTypeVehicleRequirementCreate,
    PhaseTypeVehicleRequirementRead,
    PhaseTypeVehicleRequirementUpdate,
)

router = APIRouter(prefix="/vehicle-requirements")


@router.post(
    "",
    response_model=PhaseTypeVehicleRequirementRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_vehicle_requirement(
    payload: PhaseTypeVehicleRequirementCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> PhaseTypeVehicleRequirement:
    requirement = PhaseTypeVehicleRequirement(**payload.model_dump(exclude_unset=True))
    session.add(requirement)
    await session.commit()
    await session.refresh(requirement)
    return requirement


@router.get("", response_model=list[PhaseTypeVehicleRequirementRead])
async def list_vehicle_requirements(
    limit: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
    group_id: UUID | None = Query(None),
    vehicle_type_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[PhaseTypeVehicleRequirement]:
    stmt = select(PhaseTypeVehicleRequirement)
    if group_id:
        stmt = stmt.where(PhaseTypeVehicleRequirement.group_id == group_id)
    if vehicle_type_id:
        stmt = stmt.where(
            PhaseTypeVehicleRequirement.vehicle_type_id == vehicle_type_id
        )
    stmt = stmt.order_by(
        PhaseTypeVehicleRequirement.group_id,
        PhaseTypeVehicleRequirement.vehicle_type_id,
    )
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get(
    "/{group_id}/{vehicle_type_id}",
    response_model=PhaseTypeVehicleRequirementRead,
)
async def get_vehicle_requirement(
    group_id: UUID,
    vehicle_type_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
) -> PhaseTypeVehicleRequirement:
    return await fetch_one_or_404(
        session,
        select(PhaseTypeVehicleRequirement).where(
            PhaseTypeVehicleRequirement.group_id == group_id,
            PhaseTypeVehicleRequirement.vehicle_type_id == vehicle_type_id,
        ),
        "Vehicle requirement not found",
    )


@router.patch(
    "/{group_id}/{vehicle_type_id}",
    response_model=PhaseTypeVehicleRequirementRead,
)
async def update_vehicle_requirement(
    group_id: UUID,
    vehicle_type_id: UUID,
    payload: PhaseTypeVehicleRequirementUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> PhaseTypeVehicleRequirement:
    requirement = await fetch_one_or_404(
        session,
        select(PhaseTypeVehicleRequirement).where(
            PhaseTypeVehicleRequirement.group_id == group_id,
            PhaseTypeVehicleRequirement.vehicle_type_id == vehicle_type_id,
        ),
        "Vehicle requirement not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(requirement, field, value)
    await session.commit()
    await session.refresh(requirement)
    return requirement


@router.delete(
    "/{group_id}/{vehicle_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_vehicle_requirement(
    group_id: UUID,
    vehicle_type_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
) -> None:
    requirement = await fetch_one_or_404(
        session,
        select(PhaseTypeVehicleRequirement).where(
            PhaseTypeVehicleRequirement.group_id == group_id,
            PhaseTypeVehicleRequirement.vehicle_type_id == vehicle_type_id,
        ),
        "Vehicle requirement not found",
    )
    await session.delete(requirement)
    await session.commit()
