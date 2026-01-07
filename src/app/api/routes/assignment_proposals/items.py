from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import (
    IncidentPhase,
    VehicleAssignmentProposal,
    VehicleAssignmentProposalItem,
)
from app.schemas.assignment_proposals import (
    VehicleAssignmentProposalItemCreate,
    VehicleAssignmentProposalItemRead,
    VehicleAssignmentProposalItemUpdate,
)

router = APIRouter()


async def _ensure_phase_matches_proposal(
    session: AsyncSession, proposal: VehicleAssignmentProposal, incident_phase_id: UUID
) -> IncidentPhase:
    incident_phase = await fetch_one_or_404(
        session,
        select(IncidentPhase).where(
            IncidentPhase.incident_phase_id == incident_phase_id
        ),
        "Incident phase not found",
    )
    if incident_phase.incident_id != proposal.incident_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incident phase does not belong to the same incident as the proposal",
        )
    return incident_phase


@router.post(
    "/{proposal_id}/items",
    response_model=VehicleAssignmentProposalItemRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_vehicle_assignment_proposal_item(
    proposal_id: UUID,
    payload: VehicleAssignmentProposalItemCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleAssignmentProposalItem:
    proposal = await fetch_one_or_404(
        session,
        select(VehicleAssignmentProposal).where(
            VehicleAssignmentProposal.proposal_id == proposal_id
        ),
        "Vehicle assignment proposal not found",
    )
    await _ensure_phase_matches_proposal(session, proposal, payload.incident_phase_id)

    item = VehicleAssignmentProposalItem(
        proposal_id=proposal_id, **payload.model_dump(exclude_unset=True)
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.get(
    "/{proposal_id}/items",
    response_model=list[VehicleAssignmentProposalItemRead],
)
async def list_vehicle_assignment_proposal_items(
    proposal_id: UUID,
    limit: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
    incident_phase_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[VehicleAssignmentProposalItem]:
    await fetch_one_or_404(
        session,
        select(VehicleAssignmentProposal.proposal_id).where(
            VehicleAssignmentProposal.proposal_id == proposal_id
        ),
        "Vehicle assignment proposal not found",
    )

    stmt = select(VehicleAssignmentProposalItem).where(
        VehicleAssignmentProposalItem.proposal_id == proposal_id
    )
    if incident_phase_id:
        stmt = stmt.where(
            VehicleAssignmentProposalItem.incident_phase_id == incident_phase_id
        )
    stmt = stmt.order_by(VehicleAssignmentProposalItem.proposal_rank)
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get(
    "/{proposal_id}/items/{incident_phase_id}/{vehicle_id}",
    response_model=VehicleAssignmentProposalItemRead,
)
async def get_vehicle_assignment_proposal_item(
    proposal_id: UUID,
    incident_phase_id: UUID,
    vehicle_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleAssignmentProposalItem:
    return await fetch_one_or_404(
        session,
        select(VehicleAssignmentProposalItem).where(
            VehicleAssignmentProposalItem.proposal_id == proposal_id,
            VehicleAssignmentProposalItem.incident_phase_id == incident_phase_id,
            VehicleAssignmentProposalItem.vehicle_id == vehicle_id,
        ),
        "Vehicle assignment proposal item not found",
    )


@router.patch(
    "/{proposal_id}/items/{incident_phase_id}/{vehicle_id}",
    response_model=VehicleAssignmentProposalItemRead,
)
async def update_vehicle_assignment_proposal_item(
    proposal_id: UUID,
    incident_phase_id: UUID,
    vehicle_id: UUID,
    payload: VehicleAssignmentProposalItemUpdate,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleAssignmentProposalItem:
    item = await fetch_one_or_404(
        session,
        select(VehicleAssignmentProposalItem).where(
            VehicleAssignmentProposalItem.proposal_id == proposal_id,
            VehicleAssignmentProposalItem.incident_phase_id == incident_phase_id,
            VehicleAssignmentProposalItem.vehicle_id == vehicle_id,
        ),
        "Vehicle assignment proposal item not found",
    )

    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is None:
            continue
        setattr(item, field, value)

    await session.commit()
    await session.refresh(item)
    return item


@router.delete(
    "/{proposal_id}/items/{incident_phase_id}/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_vehicle_assignment_proposal_item(
    proposal_id: UUID,
    incident_phase_id: UUID,
    vehicle_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
) -> None:
    item = await fetch_one_or_404(
        session,
        select(VehicleAssignmentProposalItem).where(
            VehicleAssignmentProposalItem.proposal_id == proposal_id,
            VehicleAssignmentProposalItem.incident_phase_id == incident_phase_id,
            VehicleAssignmentProposalItem.vehicle_id == vehicle_id,
        ),
        "Vehicle assignment proposal item not found",
    )
    await session.delete(item)
    await session.commit()
