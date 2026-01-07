from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import Energy
from app.schemas.vehicles import EnergyCreate, EnergyRead, EnergyUpdate

router = APIRouter(prefix="/energies")


@router.post("", response_model=EnergyRead, status_code=status.HTTP_201_CREATED)
async def create_energy(
    payload: EnergyCreate, session: AsyncSession = Depends(get_postgres_session)
) -> Energy:
    energy = Energy(**payload.model_dump(exclude_unset=True))
    session.add(energy)
    await session.commit()
    await session.refresh(energy)
    return energy


@router.get("", response_model=list[EnergyRead])
async def list_energies(
    limit: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[Energy]:
    stmt = select(Energy).order_by(Energy.label).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{energy_id}", response_model=EnergyRead)
async def get_energy(
    energy_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> Energy:
    return await fetch_one_or_404(
        session, select(Energy).where(Energy.energy_id == energy_id), "Energy not found"
    )


@router.patch("/{energy_id}", response_model=EnergyRead)
async def update_energy(
    energy_id: UUID,
    payload: EnergyUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> Energy:
    energy = await fetch_one_or_404(
        session, select(Energy).where(Energy.energy_id == energy_id), "Energy not found"
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(energy, field, value)
    await session.commit()
    await session.refresh(energy)
    return energy


@router.delete(
    "/{energy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_energy(
    energy_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    energy = await fetch_one_or_404(
        session, select(Energy).where(Energy.energy_id == energy_id), "Energy not found"
    )
    await session.delete(energy)
    await session.commit()
