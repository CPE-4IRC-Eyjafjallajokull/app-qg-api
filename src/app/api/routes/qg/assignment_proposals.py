from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import (
    get_current_user,
    get_postgres_session,
    get_rabbitmq_manager,
    get_sse_manager,
)
from app.api.routes.utils import fetch_one_or_404
from app.core.security import AuthenticatedUser
from app.models import (
    Incident,
    Operator,
    VehicleAssignment,
    VehicleAssignmentProposal,
    VehicleAssignmentProposalItem,
)
from app.schemas.qg.assignment_proposals import (
    QGAssignmentProposalRead,
    QGAssignmentProposalRequest,
    QGAssignmentProposalsListRead,
    QGProposalItem,
    QGRejectProposalResponse,
    QGValidateProposalResponse,
)
from app.services.events import Event, SSEManager
from app.services.messaging.queues import Queue
from app.services.messaging.rabbitmq import RabbitMQManager
from app.services.vehicle_assignments import (
    VehicleAssignmentTarget,
    build_assignment_event_payload,
    send_assignment_to_vehicles_and_wait_for_ack,
)

router = APIRouter(prefix="/assignment-proposals")


@router.get(
    "",
    response_model=QGAssignmentProposalsListRead,
)
async def list_assignment_proposals(
    session: AsyncSession = Depends(get_postgres_session),
) -> QGAssignmentProposalsListRead:
    """
    Liste toutes les propositions d'affectation de véhicules.

    Retourne les propositions générées par le moteur SDMIS, sans les géométries de route.
    """
    proposals_result = await session.execute(
        select(VehicleAssignmentProposal)
        .options(
            selectinload(VehicleAssignmentProposal.items),
            selectinload(VehicleAssignmentProposal.missing),
        )
        .order_by(VehicleAssignmentProposal.generated_at.desc())
    )
    proposals = proposals_result.scalars().all()

    assignment_proposals = [
        QGAssignmentProposalRead(
            proposal_id=proposal.proposal_id,
            incident_id=proposal.incident_id,
            generated_at=proposal.generated_at,
            validated_at=proposal.validated_at,
            rejected_at=proposal.rejected_at,
            proposals=[
                QGProposalItem(
                    incident_phase_id=item.incident_phase_id,
                    vehicle_id=item.vehicle_id,
                    distance_km=item.distance_km,
                    estimated_time_min=item.estimated_time_min,
                    energy_level=item.energy_level,
                    score=item.score,
                    rationale=item.rationale,
                )
                for item in proposal.items
            ],
            missing_by_vehicle_type={
                missing.vehicle_type_id: missing.missing_quantity
                for missing in proposal.missing
            },
        )
        for proposal in proposals
    ]

    return QGAssignmentProposalsListRead(
        assignment_proposals=assignment_proposals,
        total=len(assignment_proposals),
    )


@router.post(
    "/new",
    status_code=status.HTTP_201_CREATED,
)
async def request_assignment_proposal(
    payload: QGAssignmentProposalRequest,
    session: AsyncSession = Depends(get_postgres_session),
    user: AuthenticatedUser = Depends(get_current_user),
    sse_manager: SSEManager = Depends(get_sse_manager),
    rabbitmq: RabbitMQManager = Depends(get_rabbitmq_manager),
) -> dict[str, str]:
    await fetch_one_or_404(
        session,
        select(Incident).where(Incident.incident_id == payload.incident_id),
        "Incident not found",
    )

    envelope = {
        "event": Event.NEW_INCIDENT.value,
        "payload": {
            "incident_id": payload.incident_id,
        },
    }

    message = json.dumps(jsonable_encoder(envelope)).encode()

    try:
        await rabbitmq.enqueue(Queue.SDMIS_ENGINE, message, timeout=5.0)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Message broker unavailable",
        ) from None

    await sse_manager.notify(
        Event.VEHICLE_ASSIGNMENT_PROPOSAL_REQUEST.value,
        {
            "incident_id": payload.incident_id,
            "requested_by": user.username or user.subject,
        },
    )

    return {
        "message": "Assignment proposal request enqueued",
        "incident_id": str(payload.incident_id),
    }


@router.get(
    "/{proposal_id}",
    response_model=QGAssignmentProposalRead,
)
async def get_assignment_proposal(
    proposal_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
) -> QGAssignmentProposalRead:
    """
    Récupère le détail d'une proposition d'affectation.
    """
    proposal: VehicleAssignmentProposal = await fetch_one_or_404(
        session,
        select(VehicleAssignmentProposal)
        .options(
            selectinload(VehicleAssignmentProposal.items),
            selectinload(VehicleAssignmentProposal.missing),
        )
        .where(VehicleAssignmentProposal.proposal_id == proposal_id),
        "Proposal not found",
    )

    return QGAssignmentProposalRead(
        proposal_id=proposal.proposal_id,
        incident_id=proposal.incident_id,
        generated_at=proposal.generated_at,
        proposals=[
            QGProposalItem(
                incident_phase_id=item.incident_phase_id,
                vehicle_id=item.vehicle_id,
                distance_km=item.distance_km,
                estimated_time_min=item.estimated_time_min,
                energy_level=item.energy_level,
                score=item.score,
                rationale=item.rationale,
            )
            for item in proposal.items
        ],
        missing_by_vehicle_type={
            missing.vehicle_type_id: missing.missing_quantity
            for missing in proposal.missing
        },
    )


@router.post(
    "/{proposal_id}/validate",
    response_model=QGValidateProposalResponse,
)
async def validate_assignment_proposal(
    proposal_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
    user: AuthenticatedUser = Depends(get_current_user),
    sse_manager: SSEManager = Depends(get_sse_manager),
    rabbitmq: RabbitMQManager = Depends(get_rabbitmq_manager),
) -> QGValidateProposalResponse:
    """
    Valide une proposition d'affectation en créant les affectations pour tous les véhicules proposés.

    Envoie les événements d'affectation aux véhicules et attend que leur statut passe à "Engagé".
    Réessaie jusqu'à 5 fois avec 1 seconde d'intervalle. Si un véhicule ne passe pas en "Engagé",
    l'affectation est annulée et une erreur est retournée.
    """
    proposal: VehicleAssignmentProposal = await fetch_one_or_404(
        session,
        select(VehicleAssignmentProposal)
        .options(
            selectinload(VehicleAssignmentProposal.items).selectinload(
                VehicleAssignmentProposalItem.vehicle
            ),
            selectinload(VehicleAssignmentProposal.incident),
        )
        .where(VehicleAssignmentProposal.proposal_id == proposal_id),
        "Proposal not found",
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

    # Get operator ID from user
    operator_id = None
    if user.email:
        operator = await session.scalar(
            select(Operator).where(Operator.email == user.email)
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

    (
        engaged_targets,
        failed_targets,
    ) = await send_assignment_to_vehicles_and_wait_for_ack(
        session=session,
        rabbitmq=rabbitmq,
        targets=targets,
        incident_latitude=incident.latitude,
        incident_longitude=incident.longitude,
        engaged_status_label="Engagé",
        max_attempts=max_attempts,
        retry_delay_seconds=1.0,
    )

    engaged_vehicle_ids = {target.vehicle_id for target in engaged_targets}
    engaged_items = [
        item for item in proposal.items if item.vehicle_id in engaged_vehicle_ids
    ]
    failed_vehicles = [target.immatriculation for target in failed_targets]

    assignments_created: list[VehicleAssignment] = []
    for item in engaged_items:
        assignment = VehicleAssignment(
            vehicle_id=item.vehicle_id,
            incident_phase_id=item.incident_phase_id,
            assigned_at=now,
            assigned_by_operator_id=operator_id,
            validated_at=now,
            validated_by_operator_id=operator_id,
        )
        session.add(assignment)
        assignments_created.append(assignment)

    # Mark proposal as validated if at least one vehicle was assigned
    if engaged_items:
        proposal.validated_at = now
        await session.commit()

    # If some vehicles failed, return partial success or error
    if failed_vehicles:
        if not engaged_items:
            # No vehicles were engaged at all
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail=f"No vehicles acknowledged assignment after {max_attempts} attempts. Failed: {', '.join(failed_vehicles)}",
            )
        # Partial success - some vehicles engaged, some failed
        # We still return success but could log or notify about failures
        # TODO: Implement logging or notification for failed vehicles

    if assignments_created:
        vehicle_by_id = {
            item.vehicle_id: item.vehicle
            for item in proposal.items
            if item.vehicle is not None
        }
        for assignment in assignments_created:
            await sse_manager.notify(
                Event.VEHICLE_ASSIGNMENT.value,
                build_assignment_event_payload(
                    assignment,
                    proposal.incident_id,
                    vehicle_by_id.get(assignment.vehicle_id),
                ),
            )

    return QGValidateProposalResponse(
        proposal_id=proposal_id,
        incident_id=proposal.incident_id,
        validated_at=now,
        assignments_created=len(engaged_items),
    )


@router.post(
    "/{proposal_id}/reject",
    response_model=QGRejectProposalResponse,
)
async def reject_assignment_proposal(
    proposal_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
    user: AuthenticatedUser = Depends(get_current_user),
) -> QGRejectProposalResponse:
    """
    Rejette une proposition d'affectation.
    """
    proposal: VehicleAssignmentProposal = await fetch_one_or_404(
        session,
        select(VehicleAssignmentProposal).where(
            VehicleAssignmentProposal.proposal_id == proposal_id
        ),
        "Proposal not found",
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

    # Mark proposal as rejected
    now = datetime.now(timezone.utc)
    proposal.rejected_at = now

    await session.commit()

    return QGRejectProposalResponse(
        proposal_id=proposal_id,
        incident_id=proposal.incident_id,
        rejected_at=now,
    )
