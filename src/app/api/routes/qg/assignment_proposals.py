from __future__ import annotations

import asyncio
import json
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
    IncidentPhase,
    Operator,
    VehicleAssignmentProposal,
)
from app.schemas.qg.assignment_proposals import (
    QGAssignmentProposalRead,
    QGAssignmentProposalRequest,
    QGAssignmentProposalsListRead,
    QGProposalMissing,
    QGProposalVehicle,
    QGRejectProposalResponse,
    QGValidateProposalResponse,
)
from app.services.assignment_proposals import (
    reject_assignment_proposal as reject_assignment_proposal_service,
)
from app.services.assignment_proposals import (
    validate_assignment_proposal as validate_assignment_proposal_service,
)
from app.services.assignment_requests import (
    ASSIGNMENT_REQUEST_IN_PROGRESS_DETAIL,
    acquire_assignment_request_lock,
    release_assignment_request_lock_safely,
)
from app.services.events import Event, SSEManager
from app.services.messaging.queues import Queue
from app.services.messaging.rabbitmq import RabbitMQManager

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
            vehicles_to_send=[
                QGProposalVehicle(
                    incident_phase_id=item.incident_phase_id,
                    vehicle_id=item.vehicle_id,
                    distance_km=item.distance_km,
                    estimated_time_min=item.estimated_time_min,
                    energy_level=item.energy_level,
                    score=item.score,
                    rank=item.proposal_rank,
                )
                for item in proposal.items
            ],
            missing=[
                QGProposalMissing(
                    incident_phase_id=missing.incident_phase_id,
                    vehicle_type_id=missing.vehicle_type_id,
                    missing_quantity=missing.missing_quantity,
                )
                for missing in proposal.missing
            ],
        )
        for proposal in proposals
    ]

    return QGAssignmentProposalsListRead(
        assignment_proposals=assignment_proposals,
        total=len(assignment_proposals),
    )


@router.post(
    "/request",
    status_code=status.HTTP_201_CREATED,
)
async def request_assignment_proposal(
    payload: QGAssignmentProposalRequest,
    session: AsyncSession = Depends(get_postgres_session),
    user: AuthenticatedUser = Depends(get_current_user),
    sse_manager: SSEManager = Depends(get_sse_manager),
    rabbitmq: RabbitMQManager = Depends(get_rabbitmq_manager),
) -> dict[str, str]:
    incident_phase: IncidentPhase = await fetch_one_or_404(
        session,
        select(IncidentPhase).where(
            IncidentPhase.incident_phase_id == payload.incident_phase_id
        ),
        "Incident phase not found",
    )

    vehicles_by_type: dict[UUID, int] = {}
    for vehicle in payload.vehicles:
        vehicles_by_type[vehicle.vehicle_type_id] = (
            vehicles_by_type.get(vehicle.vehicle_type_id, 0) + vehicle.qty
        )

    if not vehicles_by_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one vehicle request is required",
        )

    operator_id = None
    if user.email:
        operator = await session.scalar(
            select(Operator).where(Operator.email == user.email)
        )
        if operator:
            operator_id = operator.operator_id

    if not await acquire_assignment_request_lock(
        session, incident_phase.incident_id, operator_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ASSIGNMENT_REQUEST_IN_PROGRESS_DETAIL,
        )

    vehicles_needed = [
        {
            "vehicle_type_id": vehicle_type_id,
            "quantity": qty,
            "incident_phase_id": payload.incident_phase_id,
        }
        for vehicle_type_id, qty in vehicles_by_type.items()
        if qty > 0
    ]

    envelope = {
        "event": Event.ASSIGNMENT_REQUEST.value,
        "payload": {
            "incident_id": incident_phase.incident_id,
            "vehicles_needed": vehicles_needed,
        },
    }

    message = json.dumps(jsonable_encoder(envelope)).encode()

    try:
        await rabbitmq.enqueue(Queue.SDMIS_ENGINE, message, timeout=5.0)
    except asyncio.TimeoutError:
        await release_assignment_request_lock_safely(
            session, incident_phase.incident_id
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Message broker unavailable",
        ) from None

    await sse_manager.notify(
        Event.ASSIGNMENT_REQUEST.value,
        {
            "incident_id": incident_phase.incident_id,
            "incident_phase_id": payload.incident_phase_id,
            "requested_by": user.username or user.subject,
        },
    )

    return {
        "message": "Assignment proposal request enqueued",
        "incident_id": str(incident_phase.incident_id),
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
        vehicles_to_send=[
            QGProposalVehicle(
                incident_phase_id=item.incident_phase_id,
                vehicle_id=item.vehicle_id,
                distance_km=item.distance_km,
                estimated_time_min=item.estimated_time_min,
                energy_level=item.energy_level,
                score=item.score,
                rank=item.proposal_rank,
            )
            for item in proposal.items
        ],
        missing=[
            QGProposalMissing(
                incident_phase_id=missing.incident_phase_id,
                vehicle_type_id=missing.vehicle_type_id,
                missing_quantity=missing.missing_quantity,
            )
            for missing in proposal.missing
        ],
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
    result = await validate_assignment_proposal_service(
        session=session,
        rabbitmq=rabbitmq,
        sse_manager=sse_manager,
        proposal_id=proposal_id,
        operator_email=user.email,
    )

    return QGValidateProposalResponse(
        proposal_id=result.proposal.proposal_id,
        incident_id=result.proposal.incident_id,
        validated_at=result.validated_at,
        assignments_created=result.assignments_created,
    )


@router.post(
    "/{proposal_id}/reject",
    response_model=QGRejectProposalResponse,
)
async def reject_assignment_proposal(
    proposal_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
    user: AuthenticatedUser = Depends(get_current_user),
    sse_manager: SSEManager = Depends(get_sse_manager),
) -> QGRejectProposalResponse:
    """
    Rejette une proposition d'affectation.
    """
    result = await reject_assignment_proposal_service(
        session=session,
        proposal_id=proposal_id,
        sse_manager=sse_manager,
    )

    return QGRejectProposalResponse(
        proposal_id=result.proposal.proposal_id,
        incident_id=result.proposal.incident_id,
        rejected_at=result.rejected_at,
    )
