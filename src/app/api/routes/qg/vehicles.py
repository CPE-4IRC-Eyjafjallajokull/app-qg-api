from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
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
from app.models import IncidentPhase, Operator, Vehicle, VehicleAssignment
from app.schemas.qg.common import QGPhaseTypeRef, QGVehicleSummary, QGVehicleTypeRef
from app.schemas.qg.engagements import QGVehicleAssignmentDetail
from app.schemas.qg.vehicles import QGVehicleAssignRequest, QGVehiclesListRead
from app.services.events import Event, SSEManager
from app.services.messaging.rabbitmq import RabbitMQManager
from app.services.vehicle_assignments import (
    VehicleAssignmentTarget,
    build_assignment_event_payload,
    send_assignment_to_vehicles_and_wait_for_ack,
)
from app.services.vehicles import VehicleService

router = APIRouter(prefix="/vehicles")


@router.get(
    "",
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
    "/assign",
    response_model=QGVehicleAssignmentDetail,
    status_code=status.HTTP_201_CREATED,
)
async def assign_vehicle_to_incident_phase(
    payload: QGVehicleAssignRequest,
    session: AsyncSession = Depends(get_postgres_session),
    user: AuthenticatedUser = Depends(get_current_user),
    sse_manager: SSEManager = Depends(get_sse_manager),
    rabbitmq: RabbitMQManager = Depends(get_rabbitmq_manager),
) -> QGVehicleAssignmentDetail:
    """
    Assigne un vehicule a une phase d'incident.

    Envoie l'affectation au vehicule, attend l'accuse, puis enregistre en base.
    """
    vehicle: Vehicle = await fetch_one_or_404(
        session,
        select(Vehicle)
        .options(selectinload(Vehicle.vehicle_type))
        .where(Vehicle.vehicle_id == payload.vehicle_id),
        "Vehicle not found",
    )

    if vehicle.vehicle_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle type not found",
        )

    incident_phase: IncidentPhase = await fetch_one_or_404(
        session,
        select(IncidentPhase)
        .options(
            selectinload(IncidentPhase.incident),
            selectinload(IncidentPhase.phase_type),
        )
        .where(IncidentPhase.incident_phase_id == payload.incident_phase_id),
        "Incident phase not found",
    )

    if incident_phase.incident is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incident not found",
        )

    if (
        incident_phase.incident.latitude is None
        or incident_phase.incident.longitude is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incident coordinates missing",
        )

    operator_id = None
    if user.email:
        operator = await session.scalar(
            select(Operator).where(Operator.email == user.email)
        )
        if operator:
            operator_id = operator.operator_id

    max_attempts = 5
    (
        engaged_targets,
        failed_targets,
    ) = await send_assignment_to_vehicles_and_wait_for_ack(
        session=session,
        rabbitmq=rabbitmq,
        targets=[
            VehicleAssignmentTarget(
                vehicle_id=vehicle.vehicle_id,
                immatriculation=vehicle.immatriculation,
            )
        ],
        incident_latitude=incident_phase.incident.latitude,
        incident_longitude=incident_phase.incident.longitude,
        engaged_status_label="Engagé",
        max_attempts=max_attempts,
        retry_delay_seconds=1.0,
    )

    if failed_targets or not engaged_targets:
        failed_vehicles = [target.immatriculation for target in failed_targets]
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=(
                f"No vehicles acknowledged assignment after {max_attempts} attempts."
                + (f" Failed: {', '.join(failed_vehicles)}" if failed_vehicles else "")
            ),
        )

    now = datetime.now(timezone.utc)
    assignment = VehicleAssignment(
        vehicle_id=vehicle.vehicle_id,
        incident_phase_id=incident_phase.incident_phase_id,
        assigned_at=now,
        assigned_by_operator_id=operator_id,
        validated_at=now,
        validated_by_operator_id=operator_id,
    )
    session.add(assignment)
    await session.commit()

    vehicle_type = vehicle.vehicle_type
    phase_type = incident_phase.phase_type

    assignment_detail = QGVehicleAssignmentDetail(
        vehicle_assignment_id=assignment.vehicle_assignment_id,
        vehicle_id=assignment.vehicle_id,
        incident_phase_id=assignment.incident_phase_id,
        assigned_at=assignment.assigned_at,
        assigned_by_operator_id=assignment.assigned_by_operator_id,
        validated_at=assignment.validated_at,
        validated_by_operator_id=assignment.validated_by_operator_id,
        unassigned_at=assignment.unassigned_at,
        notes=assignment.notes,
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

    await sse_manager.notify(
        Event.VEHICLE_ASSIGNMENT.value,
        build_assignment_event_payload(
            assignment,
            incident_phase.incident_id,
            vehicle,
        ),
    )

    return assignment_detail
