from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import InterestPointConsumable
from app.schemas.interest_points import (
    InterestPointConsumableCreate,
    InterestPointConsumableRead,
    InterestPointConsumableUpdate,
)

router = APIRouter()


@router.post(
    "/consumables",
    response_model=InterestPointConsumableRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_interest_point_consumable(
    payload: InterestPointConsumableCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> InterestPointConsumable:
    consumable = InterestPointConsumable(**payload.model_dump(exclude_unset=True))
    session.add(consumable)
    await session.commit()
    await session.refresh(consumable)
    return consumable


@router.get("/consumables", response_model=list[InterestPointConsumableRead])
async def list_interest_point_consumables(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    interest_point_id: UUID | None = Query(None),
    consumable_type_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[InterestPointConsumable]:
    stmt = select(InterestPointConsumable)
    if interest_point_id:
        stmt = stmt.where(
            InterestPointConsumable.interest_point_id == interest_point_id
        )
    if consumable_type_id:
        stmt = stmt.where(
            InterestPointConsumable.interest_point_consumable_type_id
            == consumable_type_id
        )
    stmt = stmt.order_by(InterestPointConsumable.last_update.desc())
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get(
    "/consumables/{interest_point_id}/{consumable_type_id}",
    response_model=InterestPointConsumableRead,
)
async def get_interest_point_consumable(
    interest_point_id: UUID,
    consumable_type_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
) -> InterestPointConsumable:
    return await fetch_one_or_404(
        session,
        select(InterestPointConsumable).where(
            InterestPointConsumable.interest_point_id == interest_point_id,
            InterestPointConsumable.interest_point_consumable_type_id
            == consumable_type_id,
        ),
        "Interest point consumable not found",
    )


@router.patch(
    "/consumables/{interest_point_id}/{consumable_type_id}",
    response_model=InterestPointConsumableRead,
)
async def update_interest_point_consumable(
    interest_point_id: UUID,
    consumable_type_id: UUID,
    payload: InterestPointConsumableUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> InterestPointConsumable:
    consumable = await fetch_one_or_404(
        session,
        select(InterestPointConsumable).where(
            InterestPointConsumable.interest_point_id == interest_point_id,
            InterestPointConsumable.interest_point_consumable_type_id
            == consumable_type_id,
        ),
        "Interest point consumable not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(consumable, field, value)
    await session.commit()
    await session.refresh(consumable)
    return consumable


@router.delete(
    "/consumables/{interest_point_id}/{consumable_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_interest_point_consumable(
    interest_point_id: UUID,
    consumable_type_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
) -> None:
    consumable = await fetch_one_or_404(
        session,
        select(InterestPointConsumable).where(
            InterestPointConsumable.interest_point_id == interest_point_id,
            InterestPointConsumable.interest_point_consumable_type_id
            == consumable_type_id,
        ),
        "Interest point consumable not found",
    )
    await session.delete(consumable)
    await session.commit()
