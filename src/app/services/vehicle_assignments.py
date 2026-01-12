from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Iterable, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Vehicle, VehicleAssignment, VehicleStatus
from app.services.events import Event
from app.services.messaging.queues import Queue
from app.services.messaging.rabbitmq import RabbitMQManager


@dataclass(frozen=True)
class VehicleAssignmentTarget:
    vehicle_id: UUID
    immatriculation: str


async def send_assignment_to_vehicles_and_wait_for_ack(
    session: AsyncSession,
    rabbitmq: RabbitMQManager,
    targets: Sequence[VehicleAssignmentTarget],
    incident_latitude: float,
    incident_longitude: float,
    engaged_status_label: str,
    max_attempts: int = 5,
    retry_delay_seconds: float = 1.0,
) -> tuple[list[VehicleAssignmentTarget], list[VehicleAssignmentTarget]]:
    if not targets:
        return [], []

    await _send_assignments(
        rabbitmq,
        targets,
        incident_latitude,
        incident_longitude,
    )

    pending_targets = list(targets)
    engaged_targets: list[VehicleAssignmentTarget] = []

    for attempt in range(max_attempts):
        if not pending_targets:
            break

        if retry_delay_seconds:
            await asyncio.sleep(retry_delay_seconds)

        still_pending: list[VehicleAssignmentTarget] = []
        for target in pending_targets:
            status_label = await session.scalar(
                select(VehicleStatus.label)
                .join(Vehicle, Vehicle.status_id == VehicleStatus.vehicle_status_id)
                .where(Vehicle.vehicle_id == target.vehicle_id)
            )

            if status_label == engaged_status_label:
                engaged_targets.append(target)
            else:
                still_pending.append(target)

        pending_targets = still_pending

        if pending_targets and attempt < max_attempts - 1:
            await _send_assignments(
                rabbitmq,
                pending_targets,
                incident_latitude,
                incident_longitude,
            )

    return engaged_targets, pending_targets


def build_assignment_event_payload(
    assignment: VehicleAssignment,
    incident_id: UUID,
    vehicle: Vehicle | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "incident_id": incident_id,
        "vehicle_assignment_id": assignment.vehicle_assignment_id,
        "vehicle_id": assignment.vehicle_id,
        "incident_phase_id": assignment.incident_phase_id,
        "assigned_at": assignment.assigned_at,
        "assigned_by_operator_id": assignment.assigned_by_operator_id,
        "validated_at": assignment.validated_at,
        "validated_by_operator_id": assignment.validated_by_operator_id,
        "unassigned_at": assignment.unassigned_at,
        "notes": assignment.notes,
    }

    if vehicle is not None:
        payload["vehicle_immatriculation"] = vehicle.immatriculation

    return payload


async def _send_assignments(
    rabbitmq: RabbitMQManager,
    targets: Iterable[VehicleAssignmentTarget],
    incident_latitude: float,
    incident_longitude: float,
) -> None:
    for target in targets:
        assignment_message = {
            "event": Event.VEHICLE_ASSIGNMENT.value,
            "payload": {
                "immatriculation": target.immatriculation,
                "latitude": round(incident_latitude, 6),
                "longitude": round(incident_longitude, 6),
            },
        }
        try:
            await rabbitmq.enqueue(
                Queue.VEHICLE_ASSIGNMENTS,
                json.dumps(assignment_message).encode(),
                timeout=5.0,
            )
        except asyncio.TimeoutError:
            pass
