"""Handler for vehicle and incident telemetry messages from RabbitMQ."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models import (
    Incident,
    IncidentPhase,
    Vehicle,
    VehicleAssignment,
    VehicleStatus,
)
from app.services.db.postgres import PostgresManager
from app.services.events import Event, SSEManager
from app.services.messaging.subscriber import QueueEvent
from app.services.vehicles import VehicleService

log = get_logger(__name__)


class VehiclePositionMessage(BaseModel):
    """Schema for vehicle position update from gateway."""

    immatriculation: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timestamp: datetime


class VehicleStatusMessage(BaseModel):
    """Schema for vehicle status update from gateway."""

    immatriculation: str
    status_label: str
    timestamp: datetime


class TelemetryHandler:
    """Handles vehicle telemetry events from RabbitMQ."""

    def __init__(self, postgres: PostgresManager, sse_manager: SSEManager):
        self._postgres = postgres
        self._sse_manager = sse_manager

    async def handle_vehicle_position_update(self, message: QueueEvent) -> None:
        """Handle vehicle position update from gateway."""
        if not isinstance(message.payload, dict):
            log.warning(
                "telemetry.position.invalid_payload",
                queue=message.queue,
                reason="payload_not_dict",
            )
            return

        try:
            data = VehiclePositionMessage.model_validate(message.payload)
        except ValidationError as exc:
            log.warning(
                "telemetry.position.validation_failed",
                queue=message.queue,
                errors=exc.errors(),
            )
            return

        async with self._postgres.sessionmaker()() as session:
            # Find vehicle by immatriculation
            result = await session.execute(
                select(Vehicle).where(Vehicle.immatriculation == data.immatriculation)
            )
            vehicle = result.scalar_one_or_none()

            if not vehicle:
                log.warning(
                    "telemetry.position.vehicle_not_found",
                    immatriculation=data.immatriculation,
                )
                return

            # Create position log
            vehicle_service = VehicleService(session)
            await vehicle_service.create_vehicle_position(
                vehicle.vehicle_id,
                data.latitude,
                data.longitude,
                data.timestamp,
            )

            # Notify SSE clients (frontends)
            await self._sse_manager.notify(
                Event.VEHICLE_POSITION_UPDATE.value,
                {
                    "vehicle_id": str(vehicle.vehicle_id),
                    "vehicle_immatriculation": vehicle.immatriculation,
                    "latitude": data.latitude,
                    "longitude": data.longitude,
                    "timestamp": data.timestamp.isoformat(),
                },
            )

    async def handle_vehicle_status_update(self, message: QueueEvent) -> None:
        """Handle vehicle status update from gateway."""
        if not isinstance(message.payload, dict):
            log.warning(
                "telemetry.status.invalid_payload",
                queue=message.queue,
                reason="payload_not_dict",
            )
            return

        try:
            data = VehicleStatusMessage.model_validate(message.payload)
        except ValidationError as exc:
            log.warning(
                "telemetry.status.validation_failed",
                queue=message.queue,
                errors=exc.errors(),
            )
            return

        async with self._postgres.sessionmaker()() as session:
            # Find vehicle by immatriculation
            result = await session.execute(
                select(Vehicle).where(Vehicle.immatriculation == data.immatriculation)
            )
            vehicle = result.scalar_one_or_none()

            if not vehicle:
                log.warning(
                    "telemetry.status.vehicle_not_found",
                    immatriculation=data.immatriculation,
                )
                return

            # Find status by label
            status_result = await session.execute(
                select(VehicleStatus).where(VehicleStatus.label == data.status_label)
            )
            status = status_result.scalar_one_or_none()

            if not status:
                log.warning(
                    "telemetry.status.status_not_found",
                    status_label=data.status_label,
                )
                return

            # Update vehicle status
            vehicle_service = VehicleService(session)
            await vehicle_service.update_vehicle_status(
                vehicle, status.vehicle_status_id
            )

            # Notify SSE clients (frontends)
            await self._sse_manager.notify(
                Event.VEHICLE_STATUS_UPDATE.value,
                {
                    "vehicle_id": str(vehicle.vehicle_id),
                    "vehicle_immatriculation": vehicle.immatriculation,
                    "status_label": data.status_label,
                    "timestamp": data.timestamp.isoformat(),
                },
            )

    async def handle_incident_status_update(self, message: QueueEvent) -> None:
        """Handle incident status update from gateway.

        When status=1, mark the incident phase as ended.
        The vehicle is identified by immatriculation, and we find
        its active assignment to get the incident phase.
        """
        if not isinstance(message.payload, dict):
            log.warning(
                "telemetry.incident.invalid_payload",
                queue=message.queue,
                reason="payload_not_dict",
            )
            return

        try:
            data = IncidentStatusMessage.model_validate(message.payload)
        except ValidationError as exc:
            log.warning(
                "telemetry.incident.validation_failed",
                queue=message.queue,
                errors=exc.errors(),
            )
            return

        async with self._postgres.sessionmaker()() as session:
            # Find vehicle by immatriculation
            result = await session.execute(
                select(Vehicle).where(Vehicle.immatriculation == data.immatriculation)
            )
            vehicle = result.scalar_one_or_none()

            if not vehicle:
                log.warning(
                    "telemetry.incident.vehicle_not_found",
                    immatriculation=data.immatriculation,
                )
                return

            # Find active assignment for this vehicle
            assignment_result = await session.execute(
                select(VehicleAssignment)
                .options(
                    selectinload(VehicleAssignment.incident_phase)
                    .selectinload(IncidentPhase.incident)
                    .selectinload(Incident.phases)
                )
                .where(
                    VehicleAssignment.vehicle_id == vehicle.vehicle_id,
                    VehicleAssignment.unassigned_at.is_(None),
                )
            )
            assignment = assignment_result.scalar_one_or_none()

            if not assignment:
                log.warning(
                    "telemetry.incident.no_active_assignment",
                    immatriculation=data.immatriculation,
                )
                return

            incident_phase = assignment.incident_phase
            if not incident_phase:
                log.warning(
                    "telemetry.incident.no_incident_phase",
                    immatriculation=data.immatriculation,
                )
                return

            # Status 1 = incident phase ended
            if data.status == 1:
                # 1. Mark the phase as ended
                incident_phase.ended_at = data.timestamp

                # 2. Unassign all vehicles linked to this phase
                phase_assignments_result = await session.execute(
                    select(VehicleAssignment).where(
                        VehicleAssignment.incident_phase_id
                        == incident_phase.incident_phase_id,
                        VehicleAssignment.unassigned_at.is_(None),
                    )
                )
                phase_assignments = phase_assignments_result.scalars().all()
                for phase_assignment in phase_assignments:
                    phase_assignment.unassigned_at = data.timestamp

                # 3. Check if all phases of the incident are ended
                incident = incident_phase.incident
                all_phases_ended = all(
                    phase.ended_at is not None for phase in incident.phases
                )

                incident_ended = False
                if all_phases_ended:
                    incident.ended_at = data.timestamp
                    incident_ended = True

                await session.commit()

                # Notify SSE clients (frontends)
                await self._sse_manager.notify(
                    Event.INCIDENT_STATUS_UPDATE.value,
                    {
                        "incident_id": str(incident_phase.incident_id),
                        "incident_phase_id": str(incident_phase.incident_phase_id),
                        "vehicle_immatriculation": vehicle.immatriculation,
                        "phase_ended": True,
                        "phase_ended_at": data.timestamp.isoformat(),
                        "incident_ended": incident_ended,
                        "incident_ended_at": data.timestamp.isoformat()
                        if incident_ended
                        else None,
                    },
                )

                await self._sse_manager.notify(
                    Event.INCIDENT_PHASE_UPDATE.value,
                    {
                        "incident_id": str(incident_phase.incident_id),
                        "incident_phase_id": str(incident_phase.incident_phase_id),
                        "updated_by": vehicle.immatriculation,
                        "action": "phase_ended",
                        "phase_ended_at": data.timestamp.isoformat(),
                        "incident_ended": incident_ended,
                    },
                )


class IncidentStatusMessage(BaseModel):
    """Schema for incident status update from gateway."""

    immatriculation: str
    status: int = Field(ge=0, le=255)
    timestamp: datetime
