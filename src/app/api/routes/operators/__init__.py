from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import Operator
from app.schemas.operators import OperatorCreate, OperatorRead, OperatorUpdate

router = APIRouter(tags=["operators"], prefix="/operators")


@router.post("", response_model=OperatorRead, status_code=status.HTTP_201_CREATED)
async def create_operator(
    payload: OperatorCreate, session: AsyncSession = Depends(get_postgres_session)
) -> Operator:
    operator = Operator(**payload.model_dump(exclude_unset=True))
    session.add(operator)
    await session.commit()
    await session.refresh(operator)
    return operator


@router.get("", response_model=list[OperatorRead])
async def list_operators(
    limit: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
    email: str | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[Operator]:
    stmt = select(Operator)
    if email:
        stmt = stmt.where(Operator.email == email)
    stmt = stmt.order_by(Operator.email).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{operator_id}", response_model=OperatorRead)
async def get_operator(
    operator_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> Operator:
    return await fetch_one_or_404(
        session,
        select(Operator).where(Operator.operator_id == operator_id),
        "Operator not found",
    )


@router.patch("/{operator_id}", response_model=OperatorRead)
async def update_operator(
    operator_id: UUID,
    payload: OperatorUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> Operator:
    operator = await fetch_one_or_404(
        session,
        select(Operator).where(Operator.operator_id == operator_id),
        "Operator not found",
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(operator, field, value)
    await session.commit()
    await session.refresh(operator)
    return operator


@router.delete(
    "/{operator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_operator(
    operator_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    operator = await fetch_one_or_404(
        session,
        select(Operator).where(Operator.operator_id == operator_id),
        "Operator not found",
    )
    await session.delete(operator)
    await session.commit()
