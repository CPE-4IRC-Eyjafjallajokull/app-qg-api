from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import PhaseType
from app.schemas.incidents import PhaseTypeCreate, PhaseTypeRead, PhaseTypeUpdate

router = APIRouter(prefix="/types")


@router.post("", response_model=PhaseTypeRead, status_code=status.HTTP_201_CREATED)
async def create_phase_type(
    payload: PhaseTypeCreate, session: AsyncSession = Depends(get_postgres_session)
) -> PhaseType:
    phase_type = PhaseType(**payload.model_dump(exclude_unset=True))
    session.add(phase_type)
    await session.commit()
    await session.refresh(phase_type)
    return phase_type


@router.get("", response_model=list[PhaseTypeRead])
async def list_phase_types(
    limit: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
    phase_category_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[PhaseType]:
    stmt = select(PhaseType)
    if phase_category_id:
        stmt = stmt.where(PhaseType.phase_category_id == phase_category_id)
    stmt = stmt.order_by(PhaseType.code).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{phase_type_id}", response_model=PhaseTypeRead)
async def get_phase_type(
    phase_type_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> PhaseType:
    return await fetch_one_or_404(
        session,
        select(PhaseType).where(PhaseType.phase_type_id == phase_type_id),
        "Phase type not found",
    )


@router.patch("/{phase_type_id}", response_model=PhaseTypeRead)
async def update_phase_type(
    phase_type_id: UUID,
    payload: PhaseTypeUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> PhaseType:
    phase_type = await fetch_one_or_404(
        session,
        select(PhaseType).where(PhaseType.phase_type_id == phase_type_id),
        "Phase type not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(phase_type, field, value)
    await session.commit()
    await session.refresh(phase_type)
    return phase_type


@router.delete(
    "/{phase_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_phase_type(
    phase_type_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    phase_type = await fetch_one_or_404(
        session,
        select(PhaseType).where(PhaseType.phase_type_id == phase_type_id),
        "Phase type not found",
    )
    await session.delete(phase_type)
    await session.commit()
