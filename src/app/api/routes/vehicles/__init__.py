from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.api.routes.vehicles.assignments import router as assignments_router
from app.api.routes.vehicles.consumables import (
    specs_router as consumable_spec_router,
)
from app.api.routes.vehicles.consumables import (
    stock_router as consumable_stock_router,
)
from app.api.routes.vehicles.consumables import (
    types_router as consumable_types_router,
)
from app.api.routes.vehicles.energies import router as energies_router
from app.api.routes.vehicles.position_logs import router as position_logs_router
from app.api.routes.vehicles.types import router as types_router
from app.api.routes.vehicles.vehicle_statuses import router as vehicle_statuses_router
from app.models import Vehicle
from app.schemas.vehicles import VehicleCreate, VehicleRead, VehicleUpdate

router = APIRouter(tags=["vehicles"], prefix="/vehicles")

router.include_router(consumable_stock_router)
router.include_router(consumable_spec_router)
router.include_router(consumable_types_router)
router.include_router(energies_router)
router.include_router(assignments_router)
router.include_router(vehicle_statuses_router)
router.include_router(types_router)
router.include_router(position_logs_router)


@router.post("", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    payload: VehicleCreate, session: AsyncSession = Depends(get_postgres_session)
) -> Vehicle:
    vehicle = Vehicle(**payload.model_dump(exclude_unset=True))
    session.add(vehicle)
    await session.commit()
    await session.refresh(vehicle, ["vehicle_type"])
    return vehicle


@router.get("", response_model=list[VehicleRead])
async def list_vehicles(
    limit: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
    vehicle_type_id: UUID | None = Query(None),
    status_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[Vehicle]:
    stmt = select(Vehicle).options(selectinload(Vehicle.vehicle_type))
    if vehicle_type_id:
        stmt = stmt.where(Vehicle.vehicle_type_id == vehicle_type_id)
    if status_id:
        stmt = stmt.where(Vehicle.status_id == status_id)
    stmt = stmt.order_by(Vehicle.immatriculation).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{vehicle_id}", response_model=VehicleRead)
async def get_vehicle(
    vehicle_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> Vehicle:
    return await fetch_one_or_404(
        session,
        select(Vehicle)
        .options(selectinload(Vehicle.vehicle_type))
        .where(Vehicle.vehicle_id == vehicle_id),
        "Vehicle not found",
    )


@router.patch("/{vehicle_id}", response_model=VehicleRead)
async def update_vehicle(
    vehicle_id: UUID,
    payload: VehicleUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> Vehicle:
    vehicle = await fetch_one_or_404(
        session,
        select(Vehicle)
        .options(selectinload(Vehicle.vehicle_type))
        .where(Vehicle.vehicle_id == vehicle_id),
        "Vehicle not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(vehicle, field, value)
    await session.commit()
    await session.refresh(vehicle, ["vehicle_type"])
    return vehicle


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_vehicle(
    vehicle_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    vehicle = await fetch_one_or_404(
        session,
        select(Vehicle).where(Vehicle.vehicle_id == vehicle_id),
        "Vehicle not found",
    )
    await session.delete(vehicle)
    await session.commit()
