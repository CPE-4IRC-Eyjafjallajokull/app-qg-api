from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.models import VehiclePositionLog
from app.schemas.vehicles import VehiclePositionLogCreate, VehiclePositionLogRead

router = APIRouter()


@router.post(
    "/position-logs",
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


@router.get("/position-logs", response_model=list[VehiclePositionLogRead])
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
