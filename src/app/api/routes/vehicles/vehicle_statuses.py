from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.vehicles.utils import fetch_one_or_404
from app.models import VehicleStatus
from app.schemas.vehicles import (
    VehicleStatusCreate,
    VehicleStatusRead,
    VehicleStatusUpdate,
)

router = APIRouter()


@router.post(
    "/vehicle-statuses",
    response_model=VehicleStatusRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_vehicle_status(
    payload: VehicleStatusCreate, session: AsyncSession = Depends(get_postgres_session)
) -> VehicleStatus:
    status_obj = VehicleStatus(**payload.model_dump(exclude_unset=True))
    session.add(status_obj)
    await session.commit()
    await session.refresh(status_obj)
    return status_obj


@router.get("/vehicle-statuses", response_model=list[VehicleStatusRead])
async def list_vehicle_statuses(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[VehicleStatus]:
    stmt = (
        select(VehicleStatus).order_by(VehicleStatus.label).offset(offset).limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/vehicle-statuses/{vehicle_status_id}", response_model=VehicleStatusRead)
async def get_vehicle_status(
    vehicle_status_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> VehicleStatus:
    return await fetch_one_or_404(
        session,
        select(VehicleStatus).where(
            VehicleStatus.vehicle_status_id == vehicle_status_id
        ),
        "Vehicle status not found",
    )


@router.patch("/vehicle-statuses/{vehicle_status_id}", response_model=VehicleStatusRead)
async def update_vehicle_status(
    vehicle_status_id: UUID,
    payload: VehicleStatusUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleStatus:
    status_obj = await fetch_one_or_404(
        session,
        select(VehicleStatus).where(
            VehicleStatus.vehicle_status_id == vehicle_status_id
        ),
        "Vehicle status not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(status_obj, field, value)
    await session.commit()
    await session.refresh(status_obj)
    return status_obj


@router.delete(
    "/vehicle-statuses/{vehicle_status_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_vehicle_status(
    vehicle_status_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    status_obj = await fetch_one_or_404(
        session,
        select(VehicleStatus).where(
            VehicleStatus.vehicle_status_id == vehicle_status_id
        ),
        "Vehicle status not found",
    )
    await session.delete(status_obj)
    await session.commit()
