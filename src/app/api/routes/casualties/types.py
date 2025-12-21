from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import CasualtyType
from app.schemas.casualties import (
    CasualtyTypeCreate,
    CasualtyTypeRead,
    CasualtyTypeUpdate,
)

router = APIRouter(prefix="/types")


@router.post("", response_model=CasualtyTypeRead, status_code=status.HTTP_201_CREATED)
async def create_casualty_type(
    payload: CasualtyTypeCreate, session: AsyncSession = Depends(get_postgres_session)
) -> CasualtyType:
    casualty_type = CasualtyType(**payload.model_dump(exclude_unset=True))
    session.add(casualty_type)
    await session.commit()
    await session.refresh(casualty_type)
    return casualty_type


@router.get("", response_model=list[CasualtyTypeRead])
async def list_casualty_types(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[CasualtyType]:
    stmt = select(CasualtyType).order_by(CasualtyType.code).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{casualty_type_id}", response_model=CasualtyTypeRead)
async def get_casualty_type(
    casualty_type_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> CasualtyType:
    return await fetch_one_or_404(
        session,
        select(CasualtyType).where(CasualtyType.casualty_type_id == casualty_type_id),
        "Casualty type not found",
    )


@router.patch("/{casualty_type_id}", response_model=CasualtyTypeRead)
async def update_casualty_type(
    casualty_type_id: UUID,
    payload: CasualtyTypeUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> CasualtyType:
    casualty_type = await fetch_one_or_404(
        session,
        select(CasualtyType).where(CasualtyType.casualty_type_id == casualty_type_id),
        "Casualty type not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(casualty_type, field, value)
    await session.commit()
    await session.refresh(casualty_type)
    return casualty_type


@router.delete(
    "/{casualty_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_casualty_type(
    casualty_type_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    casualty_type = await fetch_one_or_404(
        session,
        select(CasualtyType).where(CasualtyType.casualty_type_id == casualty_type_id),
        "Casualty type not found",
    )
    await session.delete(casualty_type)
    await session.commit()
