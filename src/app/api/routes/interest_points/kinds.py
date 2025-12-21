from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import InterestPointKind
from app.schemas.interest_points import (
    InterestPointKindCreate,
    InterestPointKindRead,
    InterestPointKindUpdate,
)

router = APIRouter(prefix="/kinds")


@router.post(
    "", response_model=InterestPointKindRead, status_code=status.HTTP_201_CREATED
)
async def create_interest_point_kind(
    payload: InterestPointKindCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> InterestPointKind:
    kind = InterestPointKind(**payload.model_dump(exclude_unset=True))
    session.add(kind)
    await session.commit()
    await session.refresh(kind)
    return kind


@router.get("", response_model=list[InterestPointKindRead])
async def list_interest_point_kinds(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[InterestPointKind]:
    stmt = select(InterestPointKind).order_by(InterestPointKind.label)
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{interest_point_kind_id}", response_model=InterestPointKindRead)
async def get_interest_point_kind(
    interest_point_kind_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> InterestPointKind:
    return await fetch_one_or_404(
        session,
        select(InterestPointKind).where(
            InterestPointKind.interest_point_kind_id == interest_point_kind_id
        ),
        "Interest point kind not found",
    )


@router.patch("/{interest_point_kind_id}", response_model=InterestPointKindRead)
async def update_interest_point_kind(
    interest_point_kind_id: UUID,
    payload: InterestPointKindUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> InterestPointKind:
    kind = await fetch_one_or_404(
        session,
        select(InterestPointKind).where(
            InterestPointKind.interest_point_kind_id == interest_point_kind_id
        ),
        "Interest point kind not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(kind, field, value)
    await session.commit()
    await session.refresh(kind)
    return kind


@router.delete(
    "/{interest_point_kind_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_interest_point_kind(
    interest_point_kind_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    kind = await fetch_one_or_404(
        session,
        select(InterestPointKind).where(
            InterestPointKind.interest_point_kind_id == interest_point_kind_id
        ),
        "Interest point kind not found",
    )
    await session.delete(kind)
    await session.commit()
