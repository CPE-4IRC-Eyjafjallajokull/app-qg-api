from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.vehicles.utils import fetch_one_or_404
from app.models import VehicleConsumableType
from app.schemas.vehicles import (
    VehicleConsumableTypeCreate,
    VehicleConsumableTypeRead,
    VehicleConsumableTypeUpdate,
)

router = APIRouter()


@router.post(
    "/vehicle-consumable-types",
    response_model=VehicleConsumableTypeRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_vehicle_consumable_type(
    payload: VehicleConsumableTypeCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleConsumableType:
    consumable_type = VehicleConsumableType(**payload.model_dump(exclude_unset=True))
    session.add(consumable_type)
    await session.commit()
    await session.refresh(consumable_type)
    return consumable_type


@router.get(
    "/vehicle-consumable-types",
    response_model=list[VehicleConsumableTypeRead],
)
async def list_vehicle_consumable_types(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[VehicleConsumableType]:
    stmt = (
        select(VehicleConsumableType)
        .order_by(VehicleConsumableType.label)
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get(
    "/vehicle-consumable-types/{consumable_type_id}",
    response_model=VehicleConsumableTypeRead,
)
async def get_vehicle_consumable_type(
    consumable_type_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> VehicleConsumableType:
    return await fetch_one_or_404(
        session,
        select(VehicleConsumableType).where(
            VehicleConsumableType.vehicle_consumable_type_id == consumable_type_id
        ),
        "Vehicle consumable type not found",
    )


@router.patch(
    "/vehicle-consumable-types/{consumable_type_id}",
    response_model=VehicleConsumableTypeRead,
)
async def update_vehicle_consumable_type(
    consumable_type_id: UUID,
    payload: VehicleConsumableTypeUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleConsumableType:
    consumable_type = await fetch_one_or_404(
        session,
        select(VehicleConsumableType).where(
            VehicleConsumableType.vehicle_consumable_type_id == consumable_type_id
        ),
        "Vehicle consumable type not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(consumable_type, field, value)
    await session.commit()
    await session.refresh(consumable_type)
    return consumable_type


@router.delete(
    "/vehicle-consumable-types/{consumable_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_vehicle_consumable_type(
    consumable_type_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    consumable_type = await fetch_one_or_404(
        session,
        select(VehicleConsumableType).where(
            VehicleConsumableType.vehicle_consumable_type_id == consumable_type_id
        ),
        "Vehicle consumable type not found",
    )
    await session.delete(consumable_type)
    await session.commit()
