from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.vehicles.utils import fetch_one_or_404
from app.models import Vehicle
from app.schemas.vehicles import VehicleCreate, VehicleRead, VehicleUpdate

router = APIRouter()


@router.post("/", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    payload: VehicleCreate, session: AsyncSession = Depends(get_postgres_session)
) -> Vehicle:
    vehicle = Vehicle(**payload.model_dump(exclude_unset=True))
    session.add(vehicle)
    await session.commit()
    await session.refresh(vehicle)
    return vehicle


@router.get("/", response_model=list[VehicleRead])
async def list_vehicles(
    limit: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
    vehicle_type_id: UUID | None = Query(None),
    status_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[Vehicle]:
    stmt = select(Vehicle)
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
        select(Vehicle).where(Vehicle.vehicle_id == vehicle_id),
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
        select(Vehicle).where(Vehicle.vehicle_id == vehicle_id),
        "Vehicle not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(vehicle, field, value)
    await session.commit()
    await session.refresh(vehicle)
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
