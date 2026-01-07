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
    VehicleAssignmentProposalMissing,
)
from app.schemas.assignment_proposals import (
    VehicleAssignmentProposalMissingCreate,
    VehicleAssignmentProposalMissingRead,
    VehicleAssignmentProposalMissingUpdate,
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


def _missing_entry_stmt(
    proposal_id: UUID, vehicle_type_id: UUID, incident_phase_id: UUID | None
):
    stmt = select(VehicleAssignmentProposalMissing).where(
        VehicleAssignmentProposalMissing.proposal_id == proposal_id,
        VehicleAssignmentProposalMissing.vehicle_type_id == vehicle_type_id,
    )
    if incident_phase_id is None:
        stmt = stmt.where(VehicleAssignmentProposalMissing.incident_phase_id.is_(None))
    else:
        stmt = stmt.where(
            VehicleAssignmentProposalMissing.incident_phase_id == incident_phase_id
        )
    return stmt


@router.post(
    "/{proposal_id}/missing",
    response_model=VehicleAssignmentProposalMissingRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_vehicle_assignment_proposal_missing(
    proposal_id: UUID,
    payload: VehicleAssignmentProposalMissingCreate,
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleAssignmentProposalMissing:
    proposal = await fetch_one_or_404(
        session,
        select(VehicleAssignmentProposal).where(
            VehicleAssignmentProposal.proposal_id == proposal_id
        ),
        "Vehicle assignment proposal not found",
    )

    if payload.incident_phase_id:
        await _ensure_phase_matches_proposal(
            session, proposal, payload.incident_phase_id
        )

    missing = VehicleAssignmentProposalMissing(
        proposal_id=proposal_id, **payload.model_dump(exclude_unset=True)
    )
    session.add(missing)
    await session.commit()
    await session.refresh(missing)
    return missing


@router.get(
    "/{proposal_id}/missing",
    response_model=list[VehicleAssignmentProposalMissingRead],
)
async def list_vehicle_assignment_proposal_missing(
    proposal_id: UUID,
    incident_phase_id: UUID | None = Query(None),
    limit: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_postgres_session),
) -> list[VehicleAssignmentProposalMissing]:
    await fetch_one_or_404(
        session,
        select(VehicleAssignmentProposal.proposal_id).where(
            VehicleAssignmentProposal.proposal_id == proposal_id
        ),
        "Vehicle assignment proposal not found",
    )

    stmt = select(VehicleAssignmentProposalMissing).where(
        VehicleAssignmentProposalMissing.proposal_id == proposal_id
    )
    if incident_phase_id is None:
        stmt = stmt.order_by(
            VehicleAssignmentProposalMissing.incident_phase_id,
            VehicleAssignmentProposalMissing.vehicle_type_id,
        )
    else:
        stmt = stmt.where(
            VehicleAssignmentProposalMissing.incident_phase_id == incident_phase_id
        )
        stmt = stmt.order_by(VehicleAssignmentProposalMissing.vehicle_type_id)
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get(
    "/{proposal_id}/missing/{vehicle_type_id}",
    response_model=VehicleAssignmentProposalMissingRead,
)
async def get_vehicle_assignment_proposal_missing(
    proposal_id: UUID,
    vehicle_type_id: UUID,
    incident_phase_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleAssignmentProposalMissing:
    return await fetch_one_or_404(
        session,
        _missing_entry_stmt(proposal_id, vehicle_type_id, incident_phase_id),
        "Vehicle assignment proposal missing entry not found",
    )


@router.patch(
    "/{proposal_id}/missing/{vehicle_type_id}",
    response_model=VehicleAssignmentProposalMissingRead,
)
async def update_vehicle_assignment_proposal_missing(
    proposal_id: UUID,
    vehicle_type_id: UUID,
    payload: VehicleAssignmentProposalMissingUpdate,
    incident_phase_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> VehicleAssignmentProposalMissing:
    missing = await fetch_one_or_404(
        session,
        _missing_entry_stmt(proposal_id, vehicle_type_id, incident_phase_id),
        "Vehicle assignment proposal missing entry not found",
    )

    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is None:
            continue
        setattr(missing, field, value)

    await session.commit()
    await session.refresh(missing)
    return missing


@router.delete(
    "/{proposal_id}/missing/{vehicle_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_vehicle_assignment_proposal_missing(
    proposal_id: UUID,
    vehicle_type_id: UUID,
    incident_phase_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_postgres_session),
) -> None:
    missing = await fetch_one_or_404(
        session,
        _missing_entry_stmt(proposal_id, vehicle_type_id, incident_phase_id),
        "Vehicle assignment proposal missing entry not found",
    )
    await session.delete(missing)
    await session.commit()
