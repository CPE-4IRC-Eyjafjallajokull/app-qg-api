from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.vehicles.utils import fetch_one_or_404
from app.models import VehicleTypeConsumableSpec
from app.schemas.vehicles import (
    VehicleTypeConsumableSpecCreate,
    VehicleTypeConsumableSpecRead,
    VehicleTypeConsumableSpecUpdate,
)

router = APIRouter()


@router.post(
    "/vehicle-type-consumable-specs",
    response_model=VehicleTypeConsumableSpecRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_vehicle_type_consumable_spec(
    payload: VehicleTypeConsumableSpecCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleTypeConsumableSpec:
    spec = VehicleTypeConsumableSpec(**payload.model_dump(exclude_unset=True))
    session.add(spec)
    await session.commit()
    await session.refresh(spec)
    return spec


@router.get(
    "/vehicle-type-consumable-specs",
    response_model=list[VehicleTypeConsumableSpecRead],
)
async def list_vehicle_type_consumable_specs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    vehicle_type_id: UUID | None = Query(None),
    consumable_type_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[VehicleTypeConsumableSpec]:
    stmt = select(VehicleTypeConsumableSpec)
    if vehicle_type_id:
        stmt = stmt.where(VehicleTypeConsumableSpec.vehicle_type_id == vehicle_type_id)
    if consumable_type_id:
        stmt = stmt.where(
            VehicleTypeConsumableSpec.consumable_type_id == consumable_type_id
        )
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get(
    "/vehicle-type-consumable-specs/{vehicle_type_id}/{consumable_type_id}",
    response_model=VehicleTypeConsumableSpecRead,
)
async def get_vehicle_type_consumable_spec(
    vehicle_type_id: UUID,
    consumable_type_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleTypeConsumableSpec:
    return await fetch_one_or_404(
        session,
        select(VehicleTypeConsumableSpec).where(
            VehicleTypeConsumableSpec.vehicle_type_id == vehicle_type_id,
            VehicleTypeConsumableSpec.consumable_type_id == consumable_type_id,
        ),
        "Vehicle type consumable spec not found",
    )


@router.patch(
    "/vehicle-type-consumable-specs/{vehicle_type_id}/{consumable_type_id}",
    response_model=VehicleTypeConsumableSpecRead,
)
async def update_vehicle_type_consumable_spec(
    vehicle_type_id: UUID,
    consumable_type_id: UUID,
    payload: VehicleTypeConsumableSpecUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleTypeConsumableSpec:
    spec = await fetch_one_or_404(
        session,
        select(VehicleTypeConsumableSpec).where(
            VehicleTypeConsumableSpec.vehicle_type_id == vehicle_type_id,
            VehicleTypeConsumableSpec.consumable_type_id == consumable_type_id,
        ),
        "Vehicle type consumable spec not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(spec, field, value)
    await session.commit()
    await session.refresh(spec)
    return spec


@router.delete(
    "/vehicle-type-consumable-specs/{vehicle_type_id}/{consumable_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_vehicle_type_consumable_spec(
    vehicle_type_id: UUID,
    consumable_type_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
) -> None:
    spec = await fetch_one_or_404(
        session,
        select(VehicleTypeConsumableSpec).where(
            VehicleTypeConsumableSpec.vehicle_type_id == vehicle_type_id,
            VehicleTypeConsumableSpec.consumable_type_id == consumable_type_id,
        ),
        "Vehicle type consumable spec not found",
    )
    await session.delete(spec)
    await session.commit()
