from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import (
    VehicleConsumableStock,
    VehicleConsumableType,
    VehicleTypeConsumableSpec,
)
from app.schemas.vehicles import (
    VehicleConsumableStockCreate,
    VehicleConsumableStockRead,
    VehicleConsumableStockUpdate,
    VehicleConsumableTypeCreate,
    VehicleConsumableTypeRead,
    VehicleConsumableTypeUpdate,
    VehicleTypeConsumableSpecCreate,
    VehicleTypeConsumableSpecRead,
    VehicleTypeConsumableSpecUpdate,
)

router = APIRouter(prefix="/consumables")


@router.post(
    "/types",
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
    "/types",
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
    "/types/{consumable_type_id}",
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
    "/types/{consumable_type_id}",
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
    "/types/{consumable_type_id}",
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


@router.post(
    "/stock",
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
    "/stock",
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
    "/stock/{vehicle_id}/{consumable_type_id}",
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
    "/stock/{vehicle_id}/{consumable_type_id}",
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
    "/stock/{vehicle_id}/{consumable_type_id}",
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


@router.post(
    "/specs",
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
    "/specs",
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
    "/specs/{vehicle_type_id}/{consumable_type_id}",
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
    "/specs/{vehicle_type_id}/{consumable_type_id}",
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
    "/specs/{vehicle_type_id}/{consumable_type_id}",
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
