from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import ReinforcementVehicleRequest
from app.schemas.incidents import (
    ReinforcementVehicleRequestCreate,
    ReinforcementVehicleRequestRead,
    ReinforcementVehicleRequestUpdate,
)

router = APIRouter(prefix="/reinforcement-vehicle-requests")


@router.post(
    "",
    response_model=ReinforcementVehicleRequestRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_reinforcement_vehicle_request(
    payload: ReinforcementVehicleRequestCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> ReinforcementVehicleRequest:
    request = ReinforcementVehicleRequest(**payload.model_dump(exclude_unset=True))
    session.add(request)
    await session.commit()
    await session.refresh(request)
    return request


@router.get("", response_model=list[ReinforcementVehicleRequestRead])
async def list_reinforcement_vehicle_requests(
    limit: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
    reinforcement_id: UUID | None = Query(None),
    vehicle_type_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[ReinforcementVehicleRequest]:
    stmt = select(ReinforcementVehicleRequest)
    if reinforcement_id:
        stmt = stmt.where(
            ReinforcementVehicleRequest.reinforcement_id == reinforcement_id
        )
    if vehicle_type_id:
        stmt = stmt.where(
            ReinforcementVehicleRequest.vehicle_type_id == vehicle_type_id
        )
    stmt = stmt.order_by(
        ReinforcementVehicleRequest.reinforcement_id,
        ReinforcementVehicleRequest.vehicle_type_id,
    )
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get(
    "/{reinforcement_id}/{vehicle_type_id}",
    response_model=ReinforcementVehicleRequestRead,
)
async def get_reinforcement_vehicle_request(
    reinforcement_id: UUID,
    vehicle_type_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
) -> ReinforcementVehicleRequest:
    return await fetch_one_or_404(
        session,
        select(ReinforcementVehicleRequest).where(
            ReinforcementVehicleRequest.reinforcement_id == reinforcement_id,
            ReinforcementVehicleRequest.vehicle_type_id == vehicle_type_id,
        ),
        "Reinforcement vehicle request not found",
    )


@router.patch(
    "/{reinforcement_id}/{vehicle_type_id}",
    response_model=ReinforcementVehicleRequestRead,
)
async def update_reinforcement_vehicle_request(
    reinforcement_id: UUID,
    vehicle_type_id: UUID,
    payload: ReinforcementVehicleRequestUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> ReinforcementVehicleRequest:
    request = await fetch_one_or_404(
        session,
        select(ReinforcementVehicleRequest).where(
            ReinforcementVehicleRequest.reinforcement_id == reinforcement_id,
            ReinforcementVehicleRequest.vehicle_type_id == vehicle_type_id,
        ),
        "Reinforcement vehicle request not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(request, field, value)
    await session.commit()
    await session.refresh(request)
    return request


@router.delete(
    "/{reinforcement_id}/{vehicle_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_reinforcement_vehicle_request(
    reinforcement_id: UUID,
    vehicle_type_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
) -> None:
    request = await fetch_one_or_404(
        session,
        select(ReinforcementVehicleRequest).where(
            ReinforcementVehicleRequest.reinforcement_id == reinforcement_id,
            ReinforcementVehicleRequest.vehicle_type_id == vehicle_type_id,
        ),
        "Reinforcement vehicle request not found",
    )
    await session.delete(request)
    await session.commit()
