from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.interest_points.consumable_types import (
    router as consumable_types_router,
)
from app.api.routes.interest_points.consumables import router as consumables_router
from app.api.routes.interest_points.kinds import router as kinds_router
from app.api.routes.utils import fetch_one_or_404
from app.models import InterestPoint
from app.schemas.interest_points import (
    InterestPointCreate,
    InterestPointRead,
    InterestPointUpdate,
)

router = APIRouter(tags=["interest-points"], prefix="/interest-points")

router.include_router(consumable_types_router)
router.include_router(consumables_router)
router.include_router(kinds_router)


@router.post("", response_model=InterestPointRead, status_code=status.HTTP_201_CREATED)
async def create_interest_point(
    payload: InterestPointCreate, session: AsyncSession = Depends(get_postgres_session)
) -> InterestPoint:
    print(
        "Creating interest point with payload:", payload.model_dump(exclude_unset=True)
    )
    point = InterestPoint(**payload.model_dump(exclude_unset=True))
    session.add(point)
    await session.commit()
    await session.refresh(point)
    return point


@router.get("", response_model=list[InterestPointRead])
async def list_interest_points(
    limit: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
    city: str | None = Query(None),
    zipcode: str | None = Query(None),
    interest_point_kind_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[InterestPoint]:
    stmt = select(InterestPoint)
    if city:
        stmt = stmt.where(InterestPoint.city == city)
    if zipcode:
        stmt = stmt.where(InterestPoint.zipcode == str(zipcode))
    if interest_point_kind_id:
        stmt = stmt.where(
            InterestPoint.interest_point_kind_id == interest_point_kind_id
        )
    stmt = stmt.order_by(InterestPoint.name).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{interest_point_id}", response_model=InterestPointRead)
async def get_interest_point(
    interest_point_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> InterestPoint:
    return await fetch_one_or_404(
        session,
        select(InterestPoint).where(
            InterestPoint.interest_point_id == interest_point_id
        ),
        "Interest point not found",
    )


@router.patch("/{interest_point_id}", response_model=InterestPointRead)
async def update_interest_point(
    interest_point_id: UUID,
    payload: InterestPointUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> InterestPoint:
    point = await fetch_one_or_404(
        session,
        select(InterestPoint).where(
            InterestPoint.interest_point_id == interest_point_id
        ),
        "Interest point not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(point, field, value)
    await session.commit()
    await session.refresh(point)
    return point


@router.delete(
    "/{interest_point_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_interest_point(
    interest_point_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    point = await fetch_one_or_404(
        session,
        select(InterestPoint).where(
            InterestPoint.interest_point_id == interest_point_id
        ),
        "Interest point not found",
    )
    await session.delete(point)
    await session.commit()
