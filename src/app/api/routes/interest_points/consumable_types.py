from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import InterestPointConsumableType
from app.schemas.interest_points import (
    InterestPointConsumableTypeCreate,
    InterestPointConsumableTypeRead,
    InterestPointConsumableTypeUpdate,
)

router = APIRouter()


@router.post(
    "/consumable-types",
    response_model=InterestPointConsumableTypeRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_interest_point_consumable_type(
    payload: InterestPointConsumableTypeCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> InterestPointConsumableType:
    consumable_type = InterestPointConsumableType(
        **payload.model_dump(exclude_unset=True)
    )
    session.add(consumable_type)
    await session.commit()
    await session.refresh(consumable_type)
    return consumable_type


@router.get("/consumable-types", response_model=list[InterestPointConsumableTypeRead])
async def list_interest_point_consumable_types(
    limit: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[InterestPointConsumableType]:
    stmt = select(InterestPointConsumableType).order_by(
        InterestPointConsumableType.label
    )
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get(
    "/consumable-types/{consumable_type_id}",
    response_model=InterestPointConsumableTypeRead,
)
async def get_interest_point_consumable_type(
    consumable_type_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> InterestPointConsumableType:
    return await fetch_one_or_404(
        session,
        select(InterestPointConsumableType).where(
            InterestPointConsumableType.interest_point_consumable_type_id
            == consumable_type_id
        ),
        "Interest point consumable type not found",
    )


@router.patch(
    "/consumable-types/{consumable_type_id}",
    response_model=InterestPointConsumableTypeRead,
)
async def update_interest_point_consumable_type(
    consumable_type_id: UUID,
    payload: InterestPointConsumableTypeUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> InterestPointConsumableType:
    consumable_type = await fetch_one_or_404(
        session,
        select(InterestPointConsumableType).where(
            InterestPointConsumableType.interest_point_consumable_type_id
            == consumable_type_id
        ),
        "Interest point consumable type not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(consumable_type, field, value)
    await session.commit()
    await session.refresh(consumable_type)
    return consumable_type


@router.delete(
    "/consumable-types/{consumable_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_interest_point_consumable_type(
    consumable_type_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    consumable_type = await fetch_one_or_404(
        session,
        select(InterestPointConsumableType).where(
            InterestPointConsumableType.interest_point_consumable_type_id
            == consumable_type_id
        ),
        "Interest point consumable type not found",
    )
    await session.delete(consumable_type)
    await session.commit()
