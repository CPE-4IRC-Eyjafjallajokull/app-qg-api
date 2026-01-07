from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import (
    authorize_events,
    get_current_user,
    get_postgres_session,
    get_rabbitmq_manager,
    get_sse_manager,
)
from app.api.routes.utils import fetch_one_or_404
from app.core.security import AuthenticatedUser
from app.models import (
    Casualty,
    CasualtyStatus,
    Incident,
    IncidentPhase,
    Operator,
    PhaseType,
    Vehicle,
    VehicleAssignment,
    VehicleAssignmentProposal,
    VehicleAssignmentProposalItem,
    VehicleStatus,
    VehicleType,
)
from app.schemas.incidents import IncidentDeclarationCreate, IncidentRead
from app.schemas.qg.assignment_proposals import (
    QGAssignmentProposalRead,
    QGAssignmentProposalsListRead,
    QGProposalItem,
    QGRejectProposalResponse,
    QGValidateProposalResponse,
)
from app.schemas.qg.casualties import (
    QGCasualtiesRead,
    QGCasualtyDetail,
    QGCasualtyStats,
    QGCasualtyStatusCount,
    QGCasualtyStatusRef,
    QGCasualtyTransportRead,
    QGCasualtyTypeRef,
)
from app.schemas.qg.common import QGPhaseTypeRef, QGVehicleSummary, QGVehicleTypeRef
from app.schemas.qg.engagements import (
    QGIncidentEngagementsRead,
    QGVehicleAssignmentDetail,
)
from app.schemas.qg.incidents import QGIncidentRead
from app.schemas.qg.resource_planning import (
    QGPhaseRequirements,
    QGRequirement,
    QGRequirementGap,
    QGRequirementGroup,
    QGResourcePlanningRead,
    QGVehicleAvailability,
)
from app.schemas.qg.situation import (
    QGActivePhase,
    QGCasualtiesSummary,
    QGIncidentSituationRead,
    QGIncidentSnapshot,
    QGPhaseDependency,
    QGResourcesByType,
    QGResourcesSummary,
)
from app.schemas.qg.situation import (
    QGCasualtyStatusCount as QGSituationCasualtyStatusCount,
)
from app.schemas.qg.vehicles import (
    QGVehiclePosition,
    QGVehiclePositionRead,
    QGVehiclesListRead,
    QGVehicleStatusRead,
    QGVehicleStatusUpdate,
)
from app.services.events import Event, SSEManager
from app.services.messaging.queues import Queue
from app.services.messaging.rabbitmq import RabbitMQManager
from app.services.qg import QGService
from app.services.vehicles import VehicleService

router = APIRouter(prefix="/qg", tags=["qg"])


@router.get("/live")
async def qg_livestream(
    sse_manager: SSEManager = Depends(get_sse_manager),
    _=Depends(authorize_events),
    events: list[str] | None = Query(
        default=None,
        description="Optional list of event names to subscribe to",
        alias="events",
    ),
):
    """
    Server-sent events stream for one-way, real-time updates.

    This endpoint provides:
    - Real-time internal events broadcast through the SSE manager
    - Optional filtering by event name via the `events` query parameter
    - Automatic heartbeat to keep connections alive
    - Graceful disconnection handling
    """
    return StreamingResponse(
        sse_manager.event_stream(events=events),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.post(
    "/incidents/new",
    response_model=QGIncidentRead,
    status_code=status.HTTP_201_CREATED,
)
async def declare_incident(
    payload: IncidentDeclarationCreate,
    session: AsyncSession = Depends(get_postgres_session),
    user: AuthenticatedUser = Depends(get_current_user),
    sse_manager: SSEManager = Depends(get_sse_manager),
    rabbitmq: RabbitMQManager = Depends(get_rabbitmq_manager),
) -> QGIncidentRead:
    await fetch_one_or_404(
        session,
        select(PhaseType).where(PhaseType.phase_type_id == payload.phase.phase_type_id),
        "Phase type not found",
    )

    operator_id = payload.created_by_operator_id
    if operator_id is None and user.email:
        operator = await session.scalar(
            select(Operator).where(Operator.email == user.email)
        )
        if operator:
            operator_id = operator.operator_id

    incident = Incident(
        created_by_operator_id=operator_id,
        address=payload.location.address,
        zipcode=payload.location.zipcode,
        city=payload.location.city,
        latitude=payload.location.latitude,
        longitude=payload.location.longitude,
        description=payload.description,
    )
    session.add(incident)
    await session.flush()

    started_at = payload.incident_started_at or datetime.now(timezone.utc)
    phase = IncidentPhase(
        incident_id=incident.incident_id,
        phase_type_id=payload.phase.phase_type_id,
        priority=payload.phase.priority or 0,
        started_at=started_at,
    )
    session.add(phase)
    await session.commit()

    # Reload incident with phases relationship
    incident = await session.scalar(
        select(Incident)
        .options(selectinload(Incident.phases).selectinload(IncidentPhase.phase_type))
        .where(Incident.incident_id == incident.incident_id)
    )

    response = QGIncidentRead.model_validate(incident)
    declared_by = user.username or user.subject
    incident_payload = response.model_dump()

    envelope = {
        "event": Event.NEW_INCIDENT.value,
        "payload": {
            "incident": incident_payload,
            "declared_by": declared_by,
            "status": "created",
        },
    }
    envelope.update(envelope["payload"])
    message = json.dumps(jsonable_encoder(envelope)).encode()

    try:
        await rabbitmq.enqueue(Queue.SDMIS_ENGINE, message, timeout=5.0)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Message broker unavailable",
        ) from None

    await sse_manager.notify(
        Event.NEW_INCIDENT.value,
        {
            "incident": incident_payload,
            "declared_by": declared_by,
        },
    )

    return response


@router.get(
    "/incidents/{incident_id}/situation",
    response_model=QGIncidentSituationRead,
)
async def get_incident_situation(
    incident_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> QGIncidentSituationRead:
    incident = await fetch_one_or_404(
        session,
        select(Incident).where(Incident.incident_id == incident_id),
        "Incident not found",
    )

    phases_result = await session.execute(
        select(IncidentPhase)
        .options(
            selectinload(IncidentPhase.phase_type),
            selectinload(IncidentPhase.dependencies),
        )
        .where(
            IncidentPhase.incident_id == incident_id,
            IncidentPhase.ended_at.is_(None),
        )
        .order_by(IncidentPhase.priority.desc())
    )
    phases = phases_result.scalars().all()

    phases_active: list[QGActivePhase] = []
    for phase in phases:
        phase_type = phase.phase_type
        dependencies = [
            QGPhaseDependency(
                depends_on_incident_phase_id=dependency.depends_on_incident_phase_id,
                kind=dependency.kind.value,
            )
            for dependency in phase.dependencies
        ]
        phases_active.append(
            QGActivePhase(
                incident_phase_id=phase.incident_phase_id,
                incident_id=phase.incident_id,
                phase_type_id=phase.phase_type_id,
                phase_code=phase_type.code,
                phase_label=phase_type.label,
                priority=phase.priority,
                started_at=phase.started_at,
                ended_at=phase.ended_at,
                dependencies=dependencies,
            )
        )

    assignments_result = await session.execute(
        select(VehicleAssignment)
        .join(
            IncidentPhase,
            VehicleAssignment.incident_phase_id == IncidentPhase.incident_phase_id,
        )
        .options(
            selectinload(VehicleAssignment.vehicle).selectinload(Vehicle.vehicle_type)
        )
        .where(IncidentPhase.incident_id == incident_id)
    )
    assignments = assignments_result.scalars().all()

    vehicles_assigned = len(assignments)
    vehicles_active = sum(
        1 for assignment in assignments if assignment.unassigned_at is None
    )

    by_type_map: dict[UUID, QGResourcesByType] = {}
    for assignment in assignments:
        vehicle = assignment.vehicle
        if not vehicle or not vehicle.vehicle_type:
            continue
        if assignment.unassigned_at is not None:
            continue
        vehicle_type = vehicle.vehicle_type
        entry = by_type_map.get(vehicle_type.vehicle_type_id)
        if entry is None:
            entry = QGResourcesByType(
                vehicle_type=QGVehicleTypeRef(
                    vehicle_type_id=vehicle_type.vehicle_type_id,
                    code=vehicle_type.code,
                    label=vehicle_type.label,
                ),
                count=0,
            )
            by_type_map[vehicle_type.vehicle_type_id] = entry
        entry.count += 1

    resources = QGResourcesSummary(
        vehicles_assigned=vehicles_assigned,
        vehicles_active=vehicles_active,
        by_type=sorted(by_type_map.values(), key=lambda item: item.vehicle_type.code),
    )

    casualty_rows = await session.execute(
        select(
            Casualty.casualty_status_id,
            CasualtyStatus.label,
            func.count(Casualty.casualty_id),
        )
        .join(
            CasualtyStatus,
            Casualty.casualty_status_id == CasualtyStatus.casualty_status_id,
        )
        .join(
            IncidentPhase,
            Casualty.incident_phase_id == IncidentPhase.incident_phase_id,
        )
        .where(IncidentPhase.incident_id == incident_id)
        .group_by(Casualty.casualty_status_id, CasualtyStatus.label)
    )

    by_status = [
        QGSituationCasualtyStatusCount(
            casualty_status_id=row[0],
            label=row[1],
            count=row[2],
        )
        for row in casualty_rows
    ]
    casualties = QGCasualtiesSummary(
        total=sum(status.count for status in by_status),
        by_status=sorted(by_status, key=lambda item: item.label),
    )

    incident_data = IncidentRead.model_validate(incident).model_dump()
    incident_data["status"] = QGService.get_incident_status(incident)

    return QGIncidentSituationRead(
        incident=QGIncidentSnapshot(**incident_data),
        phases_active=phases_active,
        resources=resources,
        casualties=casualties,
    )


@router.get(
    "/incidents/{incident_id}/planification-ressources",
    response_model=QGResourcePlanningRead,
)
async def get_resource_planning(
    incident_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> QGResourcePlanningRead:
    """
    Récupère les besoins en ressources pour un incident donné, ainsi que la disponibilité actuelle
    des véhicules et les écarts éventuels.

    Retourne un objet contenant :
    - Les besoins par phase et groupe de besoins
    - La disponibilité des véhicules par type
    - Les écarts entre les besoins et la disponibilité
    """
    await fetch_one_or_404(
        session,
        select(Incident).where(Incident.incident_id == incident_id),
        "Incident not found",
    )

    qg_service = QGService(session)
    phase_type_ids = await qg_service.get_active_phase_type_ids(incident_id)

    # Récupérer tous les PhaseType actifs pour initialiser la map
    active_phase_types = await qg_service.fetch_active_phase_types(phase_type_ids)

    # Initialiser phase_requirements_map avec toutes les phases actives
    phase_requirements_map: dict[UUID, QGPhaseRequirements] = {}
    for phase_type in active_phase_types:
        phase_requirements_map[phase_type.phase_type_id] = QGPhaseRequirements(
            phase_type=QGPhaseTypeRef(
                phase_type_id=phase_type.phase_type_id,
                code=phase_type.code,
                label=phase_type.label,
            ),
            groups=[],
        )

    # Récupérer et ajouter les groupes de besoins
    groups = await qg_service.fetch_requirement_groups(phase_type_ids)
    for group in groups:
        phase_type = group.phase_type
        phase_entry = phase_requirements_map.get(phase_type.phase_type_id)

        requirements = [
            QGRequirement(
                vehicle_type=QGVehicleTypeRef(
                    vehicle_type_id=requirement.vehicle_type_id,
                    code=requirement.vehicle_type.code,
                    label=requirement.vehicle_type.label,
                ),
                min_quantity=requirement.min_quantity,
                max_quantity=requirement.max_quantity,
                mandatory=requirement.mandatory,
                preference_rank=requirement.preference_rank,
            )
            for requirement in group.requirements
        ]

        if phase_entry:
            phase_entry.groups.append(
                QGRequirementGroup(
                    group_id=group.group_id,
                    label=group.label,
                    rule=group.rule,
                    min_total=group.min_total,
                    max_total=group.max_total,
                    priority=group.priority,
                    is_hard=group.is_hard,
                    requirements=sorted(
                        requirements,
                        key=lambda req: (
                            req.preference_rank is None,
                            req.preference_rank or 0,
                        ),
                    ),
                )
            )

    for phase_entry in phase_requirements_map.values():
        phase_entry.groups.sort(
            key=lambda item: (item.priority is None, item.priority or 0)
        )

    totals_result = await session.execute(
        select(
            VehicleType.vehicle_type_id,
            VehicleType.code,
            VehicleType.label,
            func.count(Vehicle.vehicle_id),
        )
        .join(Vehicle, Vehicle.vehicle_type_id == VehicleType.vehicle_type_id)
        .group_by(
            VehicleType.vehicle_type_id,
            VehicleType.code,
            VehicleType.label,
        )
    )
    totals_map = {
        row[0]: {"code": row[1], "label": row[2], "total": row[3]}
        for row in totals_result
    }

    assigned_result = await session.execute(
        select(
            Vehicle.vehicle_type_id,
            func.count(VehicleAssignment.vehicle_assignment_id),
        )
        .join(VehicleAssignment, VehicleAssignment.vehicle_id == Vehicle.vehicle_id)
        .where(VehicleAssignment.unassigned_at.is_(None))
        .group_by(Vehicle.vehicle_type_id)
    )
    assigned_map = {row[0]: row[1] for row in assigned_result}

    required_by_type, vehicle_types = QGService.aggregate_requirements(groups)

    availability = []
    for vehicle_type_id, data in totals_map.items():
        assigned = assigned_map.get(vehicle_type_id, 0)
        availability.append(
            QGVehicleAvailability(
                vehicle_type=QGVehicleTypeRef(
                    vehicle_type_id=vehicle_type_id,
                    code=data["code"],
                    label=data["label"],
                ),
                available=max(data["total"] - assigned, 0),
                assigned=assigned,
                total=data["total"],
            )
        )
    for vehicle_type_id, vehicle_type in vehicle_types.items():
        if vehicle_type_id in totals_map:
            continue
        availability.append(
            QGVehicleAvailability(
                vehicle_type=QGVehicleTypeRef(
                    vehicle_type_id=vehicle_type.vehicle_type_id,
                    code=vehicle_type.code,
                    label=vehicle_type.label,
                ),
                available=0,
                assigned=0,
                total=0,
            )
        )
    availability.sort(key=lambda item: item.vehicle_type.code)
    availability_map = {
        entry.vehicle_type.vehicle_type_id: entry.available for entry in availability
    }

    gaps = []
    for vehicle_type_id, required in required_by_type.items():
        available = availability_map.get(vehicle_type_id, 0)
        missing = max(required - available, 0)
        if missing <= 0:
            continue
        vehicle_type = vehicle_types.get(vehicle_type_id)
        if not vehicle_type:
            continue
        gaps.append(
            QGRequirementGap(
                vehicle_type=QGVehicleTypeRef(
                    vehicle_type_id=vehicle_type.vehicle_type_id,
                    code=vehicle_type.code,
                    label=vehicle_type.label,
                ),
                missing=missing,
                severity="HIGH",
            )
        )

    return QGResourcePlanningRead(
        incident_id=incident_id,
        phase_requirements=sorted(
            phase_requirements_map.values(), key=lambda item: item.phase_type.code
        ),
        availability=availability,
        gaps=sorted(gaps, key=lambda item: item.vehicle_type.code),
    )


@router.get(
    "/incidents/{incident_id}/engagements",
    response_model=QGIncidentEngagementsRead,
)
async def list_incident_engagements(
    incident_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> QGIncidentEngagementsRead:
    await fetch_one_or_404(
        session,
        select(Incident).where(Incident.incident_id == incident_id),
        "Incident not found",
    )

    assignments_result = await session.execute(
        select(VehicleAssignment)
        .join(
            IncidentPhase,
            VehicleAssignment.incident_phase_id == IncidentPhase.incident_phase_id,
        )
        .options(
            selectinload(VehicleAssignment.vehicle).selectinload(Vehicle.vehicle_type),
            selectinload(VehicleAssignment.incident_phase).selectinload(
                IncidentPhase.phase_type
            ),
        )
        .where(IncidentPhase.incident_id == incident_id)
        .order_by(VehicleAssignment.assigned_at.desc())
    )
    assignments = assignments_result.scalars().all()

    assignment_details: list[QGVehicleAssignmentDetail] = []
    for assignment in assignments:
        vehicle = assignment.vehicle
        if not vehicle or not vehicle.vehicle_type:
            continue
        vehicle_type = vehicle.vehicle_type
        phase_type = (
            assignment.incident_phase.phase_type if assignment.incident_phase else None
        )
        assignment_details.append(
            QGVehicleAssignmentDetail(
                vehicle_assignment_id=assignment.vehicle_assignment_id,
                vehicle_id=assignment.vehicle_id,
                incident_phase_id=assignment.incident_phase_id,
                assigned_at=assignment.assigned_at,
                validated_at=assignment.validated_at,
                validated_by_operator_id=assignment.validated_by_operator_id,
                unassigned_at=assignment.unassigned_at,
                assigned_by_operator_id=assignment.assigned_by_operator_id,
                vehicle=QGVehicleSummary(
                    vehicle_id=vehicle.vehicle_id,
                    immatriculation=vehicle.immatriculation,
                    vehicle_type=QGVehicleTypeRef(
                        vehicle_type_id=vehicle_type.vehicle_type_id,
                        code=vehicle_type.code,
                        label=vehicle_type.label,
                    ),
                ),
                phase_type=QGPhaseTypeRef(
                    phase_type_id=phase_type.phase_type_id,
                    code=phase_type.code,
                    label=phase_type.label,
                )
                if phase_type
                else None,
            )
        )

    return QGIncidentEngagementsRead(
        incident_id=incident_id,
        vehicle_assignments=assignment_details,
    )


@router.get(
    "/incidents/{incident_id}/casualties",
    response_model=QGCasualtiesRead,
)
async def list_incident_casualties(
    incident_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> QGCasualtiesRead:
    await fetch_one_or_404(
        session,
        select(Incident).where(Incident.incident_id == incident_id),
        "Incident not found",
    )

    casualties_result = await session.execute(
        select(Casualty)
        .join(
            IncidentPhase,
            Casualty.incident_phase_id == IncidentPhase.incident_phase_id,
        )
        .options(
            selectinload(Casualty.casualty_type),
            selectinload(Casualty.status),
            selectinload(Casualty.transports),
        )
        .where(IncidentPhase.incident_id == incident_id)
        .order_by(Casualty.reported_at.desc())
    )
    casualties = casualties_result.scalars().all()

    casualty_details: list[QGCasualtyDetail] = []
    status_counts: dict[UUID, QGCasualtyStatusCount] = {}

    for casualty in casualties:
        casualty_type = casualty.casualty_type
        status = casualty.status

        transports = sorted(
            casualty.transports,
            key=lambda transport: transport.picked_up_at
            or datetime.min.replace(tzinfo=timezone.utc),
        )
        transport_payload = [
            QGCasualtyTransportRead(
                casualty_transport_id=transport.casualty_transport_id,
                vehicle_assignment_id=transport.vehicle_assignment_id,
                picked_up_at=transport.picked_up_at,
                dropped_off_at=transport.dropped_off_at,
                picked_up_latitude=transport.picked_up_latitude,
                picked_up_longitude=transport.picked_up_longitude,
                dropped_off_latitude=transport.dropped_off_latitude,
                dropped_off_longitude=transport.dropped_off_longitude,
                notes=transport.notes,
            )
            for transport in transports
        ]

        casualty_details.append(
            QGCasualtyDetail(
                casualty_id=casualty.casualty_id,
                incident_phase_id=casualty.incident_phase_id,
                casualty_type=QGCasualtyTypeRef(
                    casualty_type_id=casualty_type.casualty_type_id,
                    code=casualty_type.code,
                    label=casualty_type.label,
                ),
                casualty_status=QGCasualtyStatusRef(
                    casualty_status_id=status.casualty_status_id,
                    label=status.label,
                ),
                reported_at=casualty.reported_at,
                notes=casualty.notes,
                transports=transport_payload,
            )
        )

        status_entry = status_counts.get(status.casualty_status_id)
        if status_entry is None:
            status_entry = QGCasualtyStatusCount(
                casualty_status_id=status.casualty_status_id,
                label=status.label,
                count=0,
            )
            status_counts[status.casualty_status_id] = status_entry
        status_entry.count += 1

    stats = QGCasualtyStats(
        total=len(casualties),
        by_status=sorted(status_counts.values(), key=lambda item: item.label),
    )

    return QGCasualtiesRead(
        incident_id=incident_id,
        casualties=casualty_details,
        stats=stats,
    )


@router.get(
    "/incidents/{incident_id}",
    response_model=QGIncidentRead,
)
async def get_incident_details(
    incident_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
) -> QGIncidentRead:
    incident = await fetch_one_or_404(
        session,
        select(Incident)
        .options(selectinload(Incident.phases).selectinload(IncidentPhase.phase_type))
        .where(Incident.incident_id == incident_id),
        "Incident not found",
    )

    # Sort phases by priority (descending) before serialization
    incident.phases = sorted(
        incident.phases, key=lambda phase: phase.priority or 0, reverse=True
    )

    return QGIncidentRead.model_validate(incident)


@router.get(
    "/incidents",
    response_model=list[QGIncidentRead],
)
async def list_incidents(
    session: AsyncSession = Depends(get_postgres_session),
) -> list[QGIncidentRead]:
    incidents_result = await session.execute(
        select(Incident)
        .options(selectinload(Incident.phases).selectinload(IncidentPhase.phase_type))
        .order_by(Incident.created_at.desc())
    )
    incidents = incidents_result.scalars().all()

    # Sort phases by priority for each incident before serialization
    for incident in incidents:
        incident.phases = sorted(
            incident.phases, key=lambda phase: phase.priority or 0, reverse=True
        )

    return [QGIncidentRead.model_validate(incident) for incident in incidents]


@router.get(
    "/vehicles",
    response_model=QGVehiclesListRead,
)
async def list_all_vehicles(
    session: AsyncSession = Depends(get_postgres_session),
) -> QGVehiclesListRead:
    """
    Liste tous les véhicules avec leurs informations complètes.

    Retourne pour chaque véhicule :
    - Informations de base (immatriculation, type, énergie, statut)
    - Point d'intérêt de base (caserne)
    - Position actuelle (dernière position connue)
    - Stocks de consommables
    - Affectation active (si le véhicule est en mission)
    """
    vehicle_service = VehicleService(session)

    vehicles = await vehicle_service.fetch_all_vehicles_with_relations()

    vehicle_ids = [vehicle.vehicle_id for vehicle in vehicles]
    positions_map = await vehicle_service.fetch_latest_positions(vehicle_ids)

    vehicle_details = [
        VehicleService.build_vehicle_detail(
            vehicle, positions_map.get(vehicle.vehicle_id)
        )
        for vehicle in vehicles
    ]

    return QGVehiclesListRead(
        vehicles=vehicle_details,
        total=len(vehicle_details),
    )


@router.post(
    "/vehicles/{vehicle_immatriculation}/position",
    response_model=QGVehiclePositionRead,
)
async def update_vehicle_position(
    vehicle_immatriculation: str,
    payload: QGVehiclePosition,
    session: AsyncSession = Depends(get_postgres_session),
    sse_manager: SSEManager = Depends(get_sse_manager),
) -> QGVehiclePositionRead:
    """
    Met à jour la position actuelle d'un véhicule identifié par son immatriculation.

    Si le véhicule n'existe pas, une erreur 404 est retournée.
    """
    vehicle: Vehicle = await fetch_one_or_404(
        session,
        select(Vehicle).where(Vehicle.immatriculation == vehicle_immatriculation),
        "Vehicle not found",
    )

    vehicle_service = VehicleService(session)
    vehicle_position = await vehicle_service.create_vehicle_position(
        vehicle.vehicle_id, payload.latitude, payload.longitude, payload.timestamp
    )

    response = QGVehiclePositionRead(
        vehicle_immatriculation=vehicle.immatriculation,
        latitude=vehicle_position.latitude,
        longitude=vehicle_position.longitude,
        timestamp=vehicle_position.timestamp,
    )

    await sse_manager.notify(
        Event.VEHICLE_POSITION_UPDATE.value,
        {
            "vehicle_id": str(vehicle.vehicle_id),
            "vehicle_immatriculation": vehicle.immatriculation,
            "latitude": vehicle_position.latitude,
            "longitude": vehicle_position.longitude,
            "timestamp": vehicle_position.timestamp.isoformat()
            if vehicle_position.timestamp
            else None,
        },
    )

    return response


@router.post(
    "/vehicles/{vehicle_immatriculation}/status",
    response_model=QGVehicleStatusRead,
)
async def update_vehicle_status(
    vehicle_immatriculation: str,
    payload: QGVehicleStatusUpdate,
    session: AsyncSession = Depends(get_postgres_session),
    sse_manager: SSEManager = Depends(get_sse_manager),
) -> QGVehicleStatusRead:
    """
    Met à jour le statut d'un véhicule identifié par son immatriculation.

    Si le véhicule n'existe pas, une erreur 404 est retournée.
    Si le statut n'existe pas, une erreur 404 est retournée.
    """
    vehicle: Vehicle = await fetch_one_or_404(
        session,
        select(Vehicle).where(Vehicle.immatriculation == vehicle_immatriculation),
        "Vehicle not found",
    )

    # Récupérer le statut par son label
    vehicle_status_record: VehicleStatus = await fetch_one_or_404(
        session,
        select(VehicleStatus).where(VehicleStatus.label == payload.status_label),
        f"Vehicle status '{payload.status_label}' not found",
    )

    vehicle_service = VehicleService(session)
    try:
        vehicle_status = await vehicle_service.update_vehicle_status(
            vehicle, vehicle_status_record.vehicle_status_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None

    response = QGVehicleStatusRead(
        vehicle_immatriculation=vehicle.immatriculation,
        status_label=vehicle_status.label,
        timestamp=payload.timestamp,
    )

    await sse_manager.notify(
        Event.VEHICLE_STATUS_UPDATE.value,
        {
            "vehicle_id": str(vehicle.vehicle_id),
            "vehicle_immatriculation": vehicle.immatriculation,
            "status_label": vehicle_status.label,
            "timestamp": payload.timestamp.isoformat(),
        },
    )

    return response


@router.get(
    "/assignment-proposals",
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


@router.get(
    "/assignment-proposals/{proposal_id}",
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
    "/assignment-proposals/{proposal_id}/validate",
    response_model=QGValidateProposalResponse,
)
async def validate_assignment_proposal(
    proposal_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
    user: AuthenticatedUser = Depends(get_current_user),
    sse_manager: SSEManager = Depends(get_sse_manager),
) -> QGValidateProposalResponse:
    """
    Valide une proposition d'affectation en créant les affectations pour tous les véhicules proposés.
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

    # Mark proposal as validated
    now = datetime.now(timezone.utc)
    proposal.validated_at = now

    # Create assignments for all vehicles in the proposal
    for item in proposal.items:
        assignment = VehicleAssignment(
            vehicle_id=item.vehicle_id,
            incident_phase_id=item.incident_phase_id,
            assigned_at=now,
            assigned_by_operator_id=operator_id,
            validated_at=now,
            validated_by_operator_id=operator_id,
        )
        session.add(assignment)

    await session.commit()

    # Send SSE event for each vehicle assignment
    incident = proposal.incident
    for item in proposal.items:
        await sse_manager.notify(
            Event.VEHICLE_ASSIGNMENT.value,
            {
                "immatriculation": item.vehicle.immatriculation,
                "latitude": round(incident.latitude, 6),
                "longitude": round(incident.longitude, 6),
            },
        )

    return QGValidateProposalResponse(
        proposal_id=proposal_id,
        incident_id=proposal.incident_id,
        validated_at=now,
        assignments_created=len(proposal.items),
    )


@router.post(
    "/assignment-proposals/{proposal_id}/reject",
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
