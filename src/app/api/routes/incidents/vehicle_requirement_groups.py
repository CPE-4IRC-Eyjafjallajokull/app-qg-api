from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import PhaseTypeVehicleRequirementGroup
from app.schemas.incidents import (
    PhaseTypeVehicleRequirementGroupCreate,
    PhaseTypeVehicleRequirementGroupRead,
    PhaseTypeVehicleRequirementGroupUpdate,
)

router = APIRouter(prefix="/vehicle-requirement-groups")


@router.post(
    "/",
    response_model=PhaseTypeVehicleRequirementGroupRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_vehicle_requirement_group(
    payload: PhaseTypeVehicleRequirementGroupCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> PhaseTypeVehicleRequirementGroup:
    group = PhaseTypeVehicleRequirementGroup(**payload.model_dump(exclude_unset=True))
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return group


@router.get("/", response_model=list[PhaseTypeVehicleRequirementGroupRead])
async def list_vehicle_requirement_groups(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    phase_type_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[PhaseTypeVehicleRequirementGroup]:
    stmt = select(PhaseTypeVehicleRequirementGroup)
    if phase_type_id:
        stmt = stmt.where(
            PhaseTypeVehicleRequirementGroup.phase_type_id == phase_type_id
        )
    stmt = stmt.order_by(PhaseTypeVehicleRequirementGroup.priority)
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{group_id}", response_model=PhaseTypeVehicleRequirementGroupRead)
async def get_vehicle_requirement_group(
    group_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> PhaseTypeVehicleRequirementGroup:
    return await fetch_one_or_404(
        session,
        select(PhaseTypeVehicleRequirementGroup).where(
            PhaseTypeVehicleRequirementGroup.group_id == group_id
        ),
        "Vehicle requirement group not found",
    )


@router.patch("/{group_id}", response_model=PhaseTypeVehicleRequirementGroupRead)
async def update_vehicle_requirement_group(
    group_id: UUID,
    payload: PhaseTypeVehicleRequirementGroupUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> PhaseTypeVehicleRequirementGroup:
    group = await fetch_one_or_404(
        session,
        select(PhaseTypeVehicleRequirementGroup).where(
            PhaseTypeVehicleRequirementGroup.group_id == group_id
        ),
        "Vehicle requirement group not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(group, field, value)
    await session.commit()
    await session.refresh(group)
    return group


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_vehicle_requirement_group(
    group_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    group = await fetch_one_or_404(
        session,
        select(PhaseTypeVehicleRequirementGroup).where(
            PhaseTypeVehicleRequirementGroup.group_id == group_id
        ),
        "Vehicle requirement group not found",
    )
    await session.delete(group)
    await session.commit()
