from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.vehicles.utils import fetch_one_or_404
from app.models import VehicleType
from app.schemas.vehicles import VehicleTypeCreate, VehicleTypeRead, VehicleTypeUpdate

router = APIRouter()


@router.post(
    "/vehicle-types",
    response_model=VehicleTypeRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_vehicle_type(
    payload: VehicleTypeCreate, session: AsyncSession = Depends(get_postgres_session)
) -> VehicleType:
    vehicle_type = VehicleType(**payload.model_dump(exclude_unset=True))
    session.add(vehicle_type)
    await session.commit()
    await session.refresh(vehicle_type)
    return vehicle_type


@router.get("/vehicle-types", response_model=list[VehicleTypeRead])
async def list_vehicle_types(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[VehicleType]:
    stmt = select(VehicleType).order_by(VehicleType.label).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/vehicle-types/{vehicle_type_id}", response_model=VehicleTypeRead)
async def get_vehicle_type(
    vehicle_type_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> VehicleType:
    return await fetch_one_or_404(
        session,
        select(VehicleType).where(VehicleType.vehicle_type_id == vehicle_type_id),
        "Vehicle type not found",
    )


@router.patch("/vehicle-types/{vehicle_type_id}", response_model=VehicleTypeRead)
async def update_vehicle_type(
    vehicle_type_id: UUID,
    payload: VehicleTypeUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleType:
    vehicle_type = await fetch_one_or_404(
        session,
        select(VehicleType).where(VehicleType.vehicle_type_id == vehicle_type_id),
        "Vehicle type not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(vehicle_type, field, value)
    await session.commit()
    await session.refresh(vehicle_type)
    return vehicle_type


@router.delete(
    "/vehicle-types/{vehicle_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_vehicle_type(
    vehicle_type_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    vehicle_type = await fetch_one_or_404(
        session,
        select(VehicleType).where(VehicleType.vehicle_type_id == vehicle_type_id),
        "Vehicle type not found",
    )
    await session.delete(vehicle_type)
    await session.commit()
