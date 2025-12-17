from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.vehicles.utils import fetch_one_or_404
from app.models import VehicleConsumableStock
from app.schemas.vehicles import (
    VehicleConsumableStockCreate,
    VehicleConsumableStockRead,
    VehicleConsumableStockUpdate,
)

router = APIRouter()


@router.post(
    "/vehicle-consumables-stock",
    response_model=VehicleConsumableStockRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_vehicle_consumable_stock(
    payload: VehicleConsumableStockCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleConsumableStock:
    stock = VehicleConsumableStock(**payload.model_dump(exclude_unset=True))
    session.add(stock)
    await session.commit()
    await session.refresh(stock)
    return stock


@router.get(
    "/vehicle-consumables-stock",
    response_model=list[VehicleConsumableStockRead],
)
async def list_vehicle_consumable_stock(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    vehicle_id: UUID | None = Query(None),
    consumable_type_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[VehicleConsumableStock]:
    stmt = select(VehicleConsumableStock)
    if vehicle_id:
        stmt = stmt.where(VehicleConsumableStock.vehicle_id == vehicle_id)
    if consumable_type_id:
        stmt = stmt.where(
            VehicleConsumableStock.consumable_type_id == consumable_type_id
        )
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get(
    "/vehicle-consumables-stock/{vehicle_id}/{consumable_type_id}",
    response_model=VehicleConsumableStockRead,
)
async def get_vehicle_consumable_stock(
    vehicle_id: UUID,
    consumable_type_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleConsumableStock:
    return await fetch_one_or_404(
        session,
        select(VehicleConsumableStock).where(
            VehicleConsumableStock.vehicle_id == vehicle_id,
            VehicleConsumableStock.consumable_type_id == consumable_type_id,
        ),
        "Vehicle consumable stock not found",
    )


@router.patch(
    "/vehicle-consumables-stock/{vehicle_id}/{consumable_type_id}",
    response_model=VehicleConsumableStockRead,
)
async def update_vehicle_consumable_stock(
    vehicle_id: UUID,
    consumable_type_id: UUID,
    payload: VehicleConsumableStockUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleConsumableStock:
    stock = await fetch_one_or_404(
        session,
        select(VehicleConsumableStock).where(
            VehicleConsumableStock.vehicle_id == vehicle_id,
            VehicleConsumableStock.consumable_type_id == consumable_type_id,
        ),
        "Vehicle consumable stock not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(stock, field, value)
    await session.commit()
    await session.refresh(stock)
    return stock


@router.delete(
    "/vehicle-consumables-stock/{vehicle_id}/{consumable_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_vehicle_consumable_stock(
    vehicle_id: UUID,
    consumable_type_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
) -> None:
    stock = await fetch_one_or_404(
        session,
        select(VehicleConsumableStock).where(
            VehicleConsumableStock.vehicle_id == vehicle_id,
            VehicleConsumableStock.consumable_type_id == consumable_type_id,
        ),
        "Vehicle consumable stock not found",
    )
    await session.delete(stock)
    await session.commit()
