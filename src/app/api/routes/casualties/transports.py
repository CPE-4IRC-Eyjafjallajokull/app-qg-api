from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import CasualtyTransport
from app.schemas.casualties import (
    CasualtyTransportCreate,
    CasualtyTransportRead,
    CasualtyTransportUpdate,
)

router = APIRouter(prefix="/transports")


@router.post(
    "",
    response_model=CasualtyTransportRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_casualty_transport(
    payload: CasualtyTransportCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> CasualtyTransport:
    transport = CasualtyTransport(**payload.model_dump(exclude_unset=True))
    session.add(transport)
    await session.commit()
    await session.refresh(transport)
    return transport


@router.get("", response_model=list[CasualtyTransportRead])
async def list_casualty_transports(
    limit: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
    casualty_id: UUID | None = Query(None),
    vehicle_assignment_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[CasualtyTransport]:
    stmt = select(CasualtyTransport)
    if casualty_id:
        stmt = stmt.where(CasualtyTransport.casualty_id == casualty_id)
    if vehicle_assignment_id:
        stmt = stmt.where(
            CasualtyTransport.vehicle_assignment_id == vehicle_assignment_id
        )
    stmt = stmt.order_by(CasualtyTransport.picked_up_at.desc())
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{casualty_transport_id}", response_model=CasualtyTransportRead)
async def get_casualty_transport(
    casualty_transport_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> CasualtyTransport:
    return await fetch_one_or_404(
        session,
        select(CasualtyTransport).where(
            CasualtyTransport.casualty_transport_id == casualty_transport_id
        ),
        "Casualty transport not found",
    )


@router.patch("/{casualty_transport_id}", response_model=CasualtyTransportRead)
async def update_casualty_transport(
    casualty_transport_id: UUID,
    payload: CasualtyTransportUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> CasualtyTransport:
    transport = await fetch_one_or_404(
        session,
        select(CasualtyTransport).where(
            CasualtyTransport.casualty_transport_id == casualty_transport_id
        ),
        "Casualty transport not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(transport, field, value)
    await session.commit()
    await session.refresh(transport)
    return transport


@router.delete(
    "/{casualty_transport_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_casualty_transport(
    casualty_transport_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    transport = await fetch_one_or_404(
        session,
        select(CasualtyTransport).where(
            CasualtyTransport.casualty_transport_id == casualty_transport_id
        ),
        "Casualty transport not found",
    )
    await session.delete(transport)
    await session.commit()
