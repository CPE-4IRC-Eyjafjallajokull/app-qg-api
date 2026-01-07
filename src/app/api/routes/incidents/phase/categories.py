from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import PhaseCategory
from app.schemas.incidents import (
    PhaseCategoryCreate,
    PhaseCategoryRead,
    PhaseCategoryUpdate,
)

router = APIRouter(prefix="/categories")


@router.post(
    "",
    response_model=PhaseCategoryRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_phase_category(
    payload: PhaseCategoryCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> PhaseCategory:
    category = PhaseCategory(**payload.model_dump(exclude_unset=True))
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


@router.get("", response_model=list[PhaseCategoryRead])
async def list_phase_categories(
    limit: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[PhaseCategory]:
    stmt = (
        select(PhaseCategory).order_by(PhaseCategory.code).offset(offset).limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{phase_category_id}", response_model=PhaseCategoryRead)
async def get_phase_category(
    phase_category_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> PhaseCategory:
    return await fetch_one_or_404(
        session,
        select(PhaseCategory).where(
            PhaseCategory.phase_category_id == phase_category_id
        ),
        "Phase category not found",
    )


@router.patch("/{phase_category_id}", response_model=PhaseCategoryRead)
async def update_phase_category(
    phase_category_id: UUID,
    payload: PhaseCategoryUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> PhaseCategory:
    category = await fetch_one_or_404(
        session,
        select(PhaseCategory).where(
            PhaseCategory.phase_category_id == phase_category_id
        ),
        "Phase category not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    await session.commit()
    await session.refresh(category)
    return category


@router.delete(
    "/{phase_category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_phase_category(
    phase_category_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    category = await fetch_one_or_404(
        session,
        select(PhaseCategory).where(
            PhaseCategory.phase_category_id == phase_category_id
        ),
        "Phase category not found",
    )
    await session.delete(category)
    await session.commit()
