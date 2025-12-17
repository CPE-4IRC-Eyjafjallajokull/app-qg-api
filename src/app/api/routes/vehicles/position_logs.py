from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.vehicles.utils import fetch_one_or_404
from app.models import VehiclePositionLog
from app.schemas.vehicles import VehiclePositionLogCreate, VehiclePositionLogRead

router = APIRouter()


@router.post(
    "/vehicle-position-logs",
    response_model=VehiclePositionLogRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_vehicle_position_log(
    payload: VehiclePositionLogCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehiclePositionLog:
    log = VehiclePositionLog(**payload.model_dump(exclude_unset=True))
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


@router.get("/vehicle-position-logs", response_model=list[VehiclePositionLogRead])
async def list_vehicle_position_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    vehicle_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[VehiclePositionLog]:
    stmt = select(VehiclePositionLog)
    if vehicle_id:
        stmt = stmt.where(VehiclePositionLog.vehicle_id == vehicle_id)
    stmt = (
        stmt.order_by(VehiclePositionLog.timestamp.desc()).offset(offset).limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get(
    "/vehicle-position-logs/{vehicle_position_id}",
    response_model=VehiclePositionLogRead,
)
async def get_vehicle_position_log(
    vehicle_position_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> VehiclePositionLog:
    return await fetch_one_or_404(
        session,
        select(VehiclePositionLog).where(
            VehiclePositionLog.vehicle_position_id == vehicle_position_id
        ),
        "Vehicle position log not found",
    )


@router.delete(
    "/vehicle-position-logs/{vehicle_position_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_vehicle_position_log(
    vehicle_position_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    log = await fetch_one_or_404(
        session,
        select(VehiclePositionLog).where(
            VehiclePositionLog.vehicle_position_id == vehicle_position_id
        ),
        "Vehicle position log not found",
    )
    await session.delete(log)
    await session.commit()
