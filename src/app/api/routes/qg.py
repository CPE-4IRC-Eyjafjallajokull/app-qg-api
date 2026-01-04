from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
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
    Casualty,
    CasualtyStatus,
    Incident,
    IncidentPhase,
    Intervention,
    Operator,
    PhaseType,
    PhaseTypeVehicleRequirement,
    PhaseTypeVehicleRequirementGroup,
    Vehicle,
    VehicleAssignment,
    VehicleType,
)
from app.schemas.incidents import (
    IncidentDeclarationCreate,
    IncidentDeclarationRead,
    IncidentPhaseRead,
    IncidentRead,
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
from app.schemas.vehicles import VehicleRead
from app.services.events import Event, SSEManager
from app.services.messaging.queues import Queue
from app.services.messaging.rabbitmq import RabbitMQManager

router = APIRouter(prefix="/qg", tags=["qg"])


def _incident_status(incident: Incident) -> str:
    return "ENDED" if incident.ended_at else "ONGOING"


async def _get_active_phase_type_ids(
    session: AsyncSession, incident_id: UUID
) -> list[UUID]:
    phase_type_rows = await session.execute(
        select(IncidentPhase.phase_type_id)
        .where(
            IncidentPhase.incident_id == incident_id,
            IncidentPhase.ended_at.is_(None),
        )
        .distinct()
    )
    return [row[0] for row in phase_type_rows]


async def _fetch_requirement_groups(
    session: AsyncSession, phase_type_ids: list[UUID]
) -> list[PhaseTypeVehicleRequirementGroup]:
    if not phase_type_ids:
        return []

    groups_result = await session.execute(
        select(PhaseTypeVehicleRequirementGroup)
        .options(
            selectinload(PhaseTypeVehicleRequirementGroup.phase_type),
            selectinload(PhaseTypeVehicleRequirementGroup.requirements).selectinload(
                PhaseTypeVehicleRequirement.vehicle_type
            ),
        )
        .where(PhaseTypeVehicleRequirementGroup.phase_type_id.in_(phase_type_ids))
    )
    return groups_result.scalars().all()


def _aggregate_requirements(
    groups: list[PhaseTypeVehicleRequirementGroup],
) -> tuple[dict[UUID, int], dict[UUID, VehicleType]]:
    required_by_type: dict[UUID, int] = {}
    vehicle_types: dict[UUID, VehicleType] = {}

    for group in groups:
        requirements = group.requirements
        group_total = 0
        for requirement in requirements:
            vehicle_types[requirement.vehicle_type_id] = requirement.vehicle_type
            count = requirement.min_quantity or 0
            group_total += count
            if count:
                required_by_type[requirement.vehicle_type_id] = (
                    required_by_type.get(requirement.vehicle_type_id, 0) + count
                )

        target_total = group_total
        if group.min_total is not None:
            target_total = max(group_total, group.min_total)

        if group.max_total is not None:
            target_total = min(target_total, group.max_total)

        if target_total > group_total and requirements:
            sorted_requirements = sorted(
                requirements,
                key=lambda req: (
                    req.preference_rank is None,
                    req.preference_rank or 0,
                ),
            )
            remaining = target_total - group_total
            index = 0
            while remaining > 0:
                requirement = sorted_requirements[index % len(sorted_requirements)]
                required_by_type[requirement.vehicle_type_id] = (
                    required_by_type.get(requirement.vehicle_type_id, 0) + 1
                )
                remaining -= 1
                index += 1

    return required_by_type, vehicle_types


@router.post(
    "/incidents/new",
    response_model=IncidentDeclarationRead,
    status_code=status.HTTP_201_CREATED,
)
async def declare_incident(
    payload: IncidentDeclarationCreate,
    session: AsyncSession = Depends(get_postgres_session),
    user: AuthenticatedUser = Depends(get_current_user),
    sse_manager: SSEManager = Depends(get_sse_manager),
    rabbitmq: RabbitMQManager = Depends(get_rabbitmq_manager),
) -> IncidentDeclarationRead:
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
    await session.refresh(incident)
    await session.refresh(phase)

    response = IncidentDeclarationRead(
        incident=IncidentRead.model_validate(incident),
        initial_phase=IncidentPhaseRead.model_validate(phase),
    )
    declared_by = user.username or user.subject
    envelope = {
        "event": Event.NEW_INCIDENT.value,
        "payload": {
            "incident": response.incident.model_dump(),
            "initial_phase": response.initial_phase.model_dump(),
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
            "incident": response.incident.model_dump(),
            "initial_phase": response.initial_phase.model_dump(),
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
    incident_data["status"] = _incident_status(incident)

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
    await fetch_one_or_404(
        session,
        select(Incident).where(Incident.incident_id == incident_id),
        "Incident not found",
    )

    phase_type_ids = await _get_active_phase_type_ids(session, incident_id)
    groups = await _fetch_requirement_groups(session, phase_type_ids)

    phase_requirements_map: dict[UUID, QGPhaseRequirements] = {}
    for group in groups:
        phase_type = group.phase_type
        phase_entry = phase_requirements_map.get(phase_type.phase_type_id)
        if phase_entry is None:
            phase_entry = QGPhaseRequirements(
                phase_type=QGPhaseTypeRef(
                    phase_type_id=phase_type.phase_type_id,
                    code=phase_type.code,
                    label=phase_type.label,
                ),
                groups=[],
            )
            phase_requirements_map[phase_type.phase_type_id] = phase_entry

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

    required_by_type, vehicle_types = _aggregate_requirements(groups)

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
    "/incidents/{incident_id}/vehicles-to-send",
    response_model=list[VehicleRead],
)
async def list_vehicles_to_send(
    incident_id: UUID, session: AsyncSession = Depends(get_postgres_session)
) -> list[Vehicle]:
    await fetch_one_or_404(
        session,
        select(Incident).where(Incident.incident_id == incident_id),
        "Incident not found",
    )

    phase_type_ids = await _get_active_phase_type_ids(session, incident_id)
    groups = await _fetch_requirement_groups(session, phase_type_ids)
    required_by_type, _ = _aggregate_requirements(groups)

    if not required_by_type:
        return []

    active_assignments = select(VehicleAssignment.vehicle_id).where(
        VehicleAssignment.unassigned_at.is_(None)
    )
    vehicles_result = await session.execute(
        select(Vehicle)
        .where(
            Vehicle.vehicle_type_id.in_(list(required_by_type.keys())),
            ~Vehicle.vehicle_id.in_(active_assignments),
        )
        .order_by(Vehicle.immatriculation)
    )
    available = vehicles_result.scalars().all()

    available_by_type: dict[UUID, list[Vehicle]] = {}
    for vehicle in available:
        available_by_type.setdefault(vehicle.vehicle_type_id, []).append(vehicle)

    selected: list[Vehicle] = []
    for vehicle_type_id, needed in required_by_type.items():
        selected.extend(available_by_type.get(vehicle_type_id, [])[:needed])

    return selected


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

    interventions_result = await session.execute(
        select(Intervention)
        .where(Intervention.incident_id == incident_id)
        .order_by(Intervention.created_at.desc())
    )
    interventions = interventions_result.scalars().all()

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
                intervention_id=assignment.intervention_id,
                vehicle_id=assignment.vehicle_id,
                incident_phase_id=assignment.incident_phase_id,
                assigned_at=assignment.assigned_at,
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
        interventions=interventions,
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
