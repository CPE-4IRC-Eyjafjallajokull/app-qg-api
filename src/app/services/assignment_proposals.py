from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Operator,
    VehicleAssignment,
    VehicleAssignmentProposal,
    VehicleAssignmentProposalItem,
)
from app.services.events import Event, SSEManager
from app.services.messaging.rabbitmq import RabbitMQManager
from app.services.vehicle_assignments import (
    VehicleAssignmentTarget,
    build_assignment_event_payload,
    create_assignments_and_wait_for_ack,
)


@dataclass(frozen=True)
class AssignmentProposalValidationResult:
    proposal: VehicleAssignmentProposal
    validated_at: datetime
    assignments_created: int


@dataclass(frozen=True)
class AssignmentProposalRejectionResult:
    proposal: VehicleAssignmentProposal
    rejected_at: datetime


async def validate_assignment_proposal(
    session: AsyncSession,
    rabbitmq: RabbitMQManager,
    sse_manager: SSEManager,
    proposal_id: UUID,
    operator_email: str | None,
) -> AssignmentProposalValidationResult:
    proposal = await session.scalar(
        select(VehicleAssignmentProposal)
        .options(
            selectinload(VehicleAssignmentProposal.items).selectinload(
                VehicleAssignmentProposalItem.vehicle
            ),
            selectinload(VehicleAssignmentProposal.incident),
        )
        .where(VehicleAssignmentProposal.proposal_id == proposal_id)
    )

    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found",
        )

    if proposal.validated_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proposal already validated",
        )

    if proposal.rejected_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proposal already rejected",
        )

    if not proposal.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No vehicles in proposal",
        )

    operator_id = None
    if operator_email:
        operator = await session.scalar(
            select(Operator).where(Operator.email == operator_email)
        )
        if operator:
            operator_id = operator.operator_id

    incident = proposal.incident
    if incident.latitude is None or incident.longitude is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incident coordinates missing",
        )

    max_attempts = 5
    now = datetime.now(timezone.utc)

    targets = [
        VehicleAssignmentTarget(
            vehicle_id=item.vehicle_id,
            immatriculation=item.vehicle.immatriculation,
        )
        for item in proposal.items
    ]

    assignments = [
        VehicleAssignment(
            vehicle_id=item.vehicle_id,
            incident_phase_id=item.incident_phase_id,
            assigned_at=now,
            assigned_by_operator_id=operator_id,
        )
        for item in proposal.items
    ]
    (
        engaged_assignments,
        failed_targets,
    ) = await create_assignments_and_wait_for_ack(
        session=session,
        rabbitmq=rabbitmq,
        assignments=assignments,
        targets=targets,
        incident_latitude=incident.latitude,
        incident_longitude=incident.longitude,
        engaged_status_label="Engagé",
        validated_by_operator_id=operator_id,
        max_attempts=max_attempts,
        retry_delay_seconds=1.0,
    )

    engaged_vehicle_ids = {assignment.vehicle_id for assignment in engaged_assignments}
    engaged_items = [
        item for item in proposal.items if item.vehicle_id in engaged_vehicle_ids
    ]
    failed_vehicles = [target.immatriculation for target in failed_targets]

    if engaged_items:
        proposal.validated_at = now
        await session.commit()

    if failed_vehicles and not engaged_items:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=(
                "No vehicles acknowledged assignment after "
                f"{max_attempts} attempts. Failed: {', '.join(failed_vehicles)}"
            ),
        )

    if engaged_assignments:
        vehicle_by_id = {
            item.vehicle_id: item.vehicle
            for item in proposal.items
            if item.vehicle is not None
        }
        for assignment in engaged_assignments:
            await sse_manager.notify(
                Event.VEHICLE_ASSIGNMENT.value,
                build_assignment_event_payload(
                    assignment,
                    proposal.incident_id,
                    vehicle_by_id.get(assignment.vehicle_id),
                ),
            )

    if engaged_items:
        await sse_manager.notify(
            Event.ASSIGNMENT_PROPOSAL_ACCEPTED.value,
            {
                "proposal_id": str(proposal.proposal_id),
                "incident_id": str(proposal.incident_id),
                "validated_at": now.isoformat(),
                "assignments_created": len(engaged_items),
            },
        )

    return AssignmentProposalValidationResult(
        proposal=proposal,
        validated_at=now,
        assignments_created=len(engaged_items),
    )


async def reject_assignment_proposal(
    session: AsyncSession,
    proposal_id: UUID,
    sse_manager: SSEManager,
) -> AssignmentProposalRejectionResult:
    proposal = await session.scalar(
        select(VehicleAssignmentProposal).where(
            VehicleAssignmentProposal.proposal_id == proposal_id
        )
    )

    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found",
        )

    if proposal.validated_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proposal already validated",
        )

    if proposal.rejected_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proposal already rejected",
        )

    now = datetime.now(timezone.utc)
    proposal.rejected_at = now
    await session.commit()

    await sse_manager.notify(
        Event.ASSIGNMENT_PROPOSAL_REFUSED.value,
        {
            "proposal_id": str(proposal.proposal_id),
            "incident_id": str(proposal.incident_id),
            "rejected_at": now.isoformat(),
        },
    )

    return AssignmentProposalRejectionResult(
        proposal=proposal,
        rejected_at=now,
    )
