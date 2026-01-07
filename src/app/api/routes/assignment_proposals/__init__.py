from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_postgres_session
from app.api.routes.assignment_proposals.items import router as items_router
from app.api.routes.assignment_proposals.missing import router as missing_router
from app.api.routes.utils import fetch_one_or_404
from app.models import (
    Incident,
    VehicleAssignmentProposal,
)
from app.schemas.assignment_proposals import (
    VehicleAssignmentProposalCreate,
    VehicleAssignmentProposalRead,
    VehicleAssignmentProposalUpdate,
)

router = APIRouter(
    prefix="/vehicle-assignment-proposals", tags=["vehicle_assignment_proposals"]
)

router.include_router(items_router)
router.include_router(missing_router)


def _proposal_with_relations_stmt(proposal_id: UUID):
    return (
        select(VehicleAssignmentProposal)
        .options(
            selectinload(VehicleAssignmentProposal.items),
            selectinload(VehicleAssignmentProposal.missing),
        )
        .where(VehicleAssignmentProposal.proposal_id == proposal_id)
    )


async def _fetch_proposal_or_404(
    session: AsyncSession, proposal_id: UUID
) -> VehicleAssignmentProposal:
    return await fetch_one_or_404(
        session,
        _proposal_with_relations_stmt(proposal_id),
        "Vehicle assignment proposal not found",
    )


@router.post(
    "",
    response_model=VehicleAssignmentProposalRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_vehicle_assignment_proposal(
    payload: VehicleAssignmentProposalCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleAssignmentProposal:
    await fetch_one_or_404(
        session,
        select(Incident).where(Incident.incident_id == payload.incident_id),
        "Incident not found",
    )

    proposal_data = payload.model_dump(exclude_unset=True)
    if proposal_data.get("received_at") is None:
        proposal_data.pop("received_at", None)
    proposal = VehicleAssignmentProposal(**proposal_data)
    session.add(proposal)
    await session.commit()

    return await _fetch_proposal_or_404(session, proposal.proposal_id)


@router.get("", response_model=list[VehicleAssignmentProposalRead])
async def list_vehicle_assignment_proposals(
    limit: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
    incident_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[VehicleAssignmentProposal]:
    stmt = select(VehicleAssignmentProposal).options(
        selectinload(VehicleAssignmentProposal.items),
        selectinload(VehicleAssignmentProposal.missing),
    )
    if incident_id:
        stmt = stmt.where(VehicleAssignmentProposal.incident_id == incident_id)
    stmt = stmt.order_by(VehicleAssignmentProposal.generated_at.desc())
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{proposal_id}", response_model=VehicleAssignmentProposalRead)
async def get_vehicle_assignment_proposal(
    proposal_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> VehicleAssignmentProposal:
    return await _fetch_proposal_or_404(session, proposal_id)


@router.patch("/{proposal_id}", response_model=VehicleAssignmentProposalRead)
async def update_vehicle_assignment_proposal(
    proposal_id: UUID,
    payload: VehicleAssignmentProposalUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleAssignmentProposal:
    proposal = await fetch_one_or_404(
        session,
        select(VehicleAssignmentProposal).where(
            VehicleAssignmentProposal.proposal_id == proposal_id
        ),
        "Vehicle assignment proposal not found",
    )

    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is None:
            continue
        setattr(proposal, field, value)

    await session.commit()
    return await _fetch_proposal_or_404(session, proposal_id)


@router.delete(
    "/{proposal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_vehicle_assignment_proposal(
    proposal_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> None:
    proposal = await fetch_one_or_404(
        session,
        select(VehicleAssignmentProposal).where(
            VehicleAssignmentProposal.proposal_id == proposal_id
        ),
        "Vehicle assignment proposal not found",
    )
    await session.delete(proposal)
    await session.commit()
