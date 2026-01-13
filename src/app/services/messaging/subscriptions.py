from __future__ import annotations

import asyncio
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger
from app.models import (
    Incident,
    VehicleAssignmentProposal,
    VehicleAssignmentProposalItem,
    VehicleAssignmentProposalMissing,
    VehicleAssignmentRequest,
)
from app.schemas.routing.route import LineStringGeometry
from app.services.assignment_proposals import (
    validate_assignment_proposal as validate_assignment_proposal_service,
)
from app.services.db.postgres import PostgresManager
from app.services.events import Event, SSEManager
from app.services.messaging.queues import Queue, subscription_queues
from app.services.messaging.rabbitmq import RabbitMQManager
from app.services.messaging.subscriber import (
    QueueEvent,
    RabbitMQSubscriptionService,
)
from app.services.messaging.telemetry_handler import TelemetryHandler

log = get_logger(__name__)


# --- Pydantic schemas for RabbitMQ message parsing ---


class ProposalVehicleMessage(BaseModel):
    incident_phase_id: UUID
    vehicle_id: UUID
    distance_km: float = Field(ge=0)
    estimated_time_min: float = Field(ge=0)
    route_geometry: LineStringGeometry
    energy_level: float = Field(ge=0, le=1)
    score: float = Field(ge=0, le=1)
    rank: int = Field(ge=1)


class MissingVehicleMessage(BaseModel):
    incident_phase_id: UUID
    vehicle_type_id: UUID
    missing_quantity: int = Field(ge=0)


class ProposalMessage(BaseModel):
    proposal_id: UUID
    incident_id: UUID
    generated_at: datetime
    vehicles_to_send: list[ProposalVehicleMessage] = []
    missing: list[MissingVehicleMessage] = []


class ApplicationSubscriptions(RabbitMQSubscriptionService):
    """Application-specific event handlers wired on top of the base subscriber."""

    _AUTO_ACCEPT_DELAY_SECONDS = 120.0

    def __init__(
        self,
        rabbitmq: RabbitMQManager,
        postgres: PostgresManager,
        sse_manager: SSEManager,
        queues: list[Queue] | tuple[Queue, ...] = subscription_queues(),
    ):
        super().__init__(rabbitmq, queues)
        self._sse_manager = sse_manager
        self._postgres = postgres
        self._telemetry_handler = TelemetryHandler(postgres, sse_manager)
        self._auto_accept_tasks: set[asyncio.Task[None]] = set()

        # Register event handlers once at init time
        self.on(
            Event.ASSIGNMENT_PROPOSAL.value,
            self._handle_vehicle_assignment_proposal,
        )
        self.on(
            Event.VEHICLE_POSITION_UPDATE.value,
            self._telemetry_handler.handle_vehicle_position_update,
        )
        self.on(
            Event.VEHICLE_STATUS_UPDATE.value,
            self._telemetry_handler.handle_vehicle_status_update,
        )
        self.on(
            Event.INCIDENT_STATUS_UPDATE.value,
            self._telemetry_handler.handle_incident_status_update,
        )

    async def _handle_vehicle_assignment_proposal(self, message: QueueEvent) -> None:
        """Handle vehicle assignment proposal: store in DB and forward to SSE."""
        if not isinstance(message.payload, dict):
            log.warning(
                "subscription.assignment_proposal.invalid_payload",
                queue=message.queue,
                reason="payload_not_dict",
            )
            return

        # Parse with Pydantic
        try:
            data = ProposalMessage.model_validate(message.payload)
        except ValidationError as exc:
            log.warning(
                "subscription.assignment_proposal.validation_failed",
                queue=message.queue,
                errors=exc.errors(),
            )
            return

        # Store in database
        await self._store_proposal(data, message.queue)

        # Forward to SSE without route_geometry
        sse_payload = self._build_sse_payload(data)
        await self._sse_manager.notify(Event.ASSIGNMENT_PROPOSAL.value, sse_payload)
        log.info(
            "subscription.event.forwarded",
            queue=message.queue,
            event_name=Event.ASSIGNMENT_PROPOSAL.value,
        )
        self._schedule_auto_accept(data.proposal_id)

    def _schedule_auto_accept(self, proposal_id: UUID) -> None:
        task = asyncio.create_task(self._auto_accept_assignment_proposal(proposal_id))
        self._auto_accept_tasks.add(task)
        task.add_done_callback(self._on_auto_accept_done)

    def _on_auto_accept_done(self, task: asyncio.Task[None]) -> None:
        self._auto_accept_tasks.discard(task)
        try:
            task.result()
        except asyncio.CancelledError:
            return
        except Exception as exc:
            log.error(
                "subscription.assignment_proposal.auto_accept_task_failed",
                error=str(exc),
            )

    async def _auto_accept_assignment_proposal(self, proposal_id: UUID) -> None:
        await asyncio.sleep(self._AUTO_ACCEPT_DELAY_SECONDS)

        async with self._postgres.sessionmaker()() as session:
            try:
                result = await validate_assignment_proposal_service(
                    session=session,
                    rabbitmq=self._rabbitmq,
                    sse_manager=self._sse_manager,
                    proposal_id=proposal_id,
                    operator_email=None,
                )
            except Exception as exc:
                status_code = getattr(exc, "status_code", None)
                if status_code in {400, 404}:
                    log.info(
                        "subscription.assignment_proposal.auto_accept_skipped",
                        proposal_id=str(proposal_id),
                        status_code=status_code,
                        detail=getattr(exc, "detail", str(exc)),
                    )
                else:
                    log.error(
                        "subscription.assignment_proposal.auto_accept_failed",
                        proposal_id=str(proposal_id),
                        status_code=status_code,
                        error=str(exc),
                    )
                return

        log.info(
            "subscription.assignment_proposal.auto_accept_succeeded",
            proposal_id=str(proposal_id),
            assignments_created=result.assignments_created,
        )

    async def _store_proposal(self, data: ProposalMessage, queue: str) -> None:
        """Store proposal, items and missing in PostgreSQL."""
        async with self._postgres.sessionmaker()() as session:
            # Check duplicate
            if await session.get(VehicleAssignmentProposal, data.proposal_id):
                log.info(
                    "subscription.assignment_proposal.duplicate",
                    proposal_id=data.proposal_id,
                )
                return

            # Check incident exists
            result = await session.execute(
                select(Incident.incident_id).where(
                    Incident.incident_id == data.incident_id
                )
            )
            if not result.scalar_one_or_none():
                log.warning(
                    "subscription.assignment_proposal.incident_missing",
                    proposal_id=data.proposal_id,
                    incident_id=data.incident_id,
                )
                return

            # Create proposal
            proposal = VehicleAssignmentProposal(
                proposal_id=data.proposal_id,
                incident_id=data.incident_id,
                generated_at=data.generated_at,
            )
            session.add(proposal)

            # Create items using rank provided by the engine
            for item in data.vehicles_to_send:
                session.add(
                    VehicleAssignmentProposalItem(
                        proposal_id=data.proposal_id,
                        incident_phase_id=item.incident_phase_id,
                        vehicle_id=item.vehicle_id,
                        proposal_rank=item.rank,
                        distance_km=item.distance_km,
                        estimated_time_min=int(item.estimated_time_min),
                        route_geometry=item.route_geometry.model_dump(),
                        energy_level=item.energy_level,
                        score=item.score,
                    )
                )

            # Create missing entries per phase
            for missing in data.missing:
                session.add(
                    VehicleAssignmentProposalMissing(
                        proposal_id=data.proposal_id,
                        incident_phase_id=missing.incident_phase_id,
                        vehicle_type_id=missing.vehicle_type_id,
                        missing_quantity=missing.missing_quantity,
                    )
                )

            try:
                await session.execute(
                    delete(VehicleAssignmentRequest).where(
                        VehicleAssignmentRequest.incident_id == data.incident_id
                    )
                )
                await session.commit()
            except SQLAlchemyError as exc:
                await session.rollback()
                log.error(
                    "subscription.assignment_proposal.save_failed",
                    proposal_id=data.proposal_id,
                    error=str(exc),
                )
                return

        log.info(
            "subscription.assignment_proposal.saved",
            proposal_id=data.proposal_id,
            incident_id=data.incident_id,
            items=len(data.vehicles_to_send),
            missing=len(data.missing),
        )

    @staticmethod
    def _build_sse_payload(data: ProposalMessage) -> dict:
        """Build SSE payload without route_geometry."""
        return {
            "proposal_id": str(data.proposal_id),
            "incident_id": str(data.incident_id),
            "generated_at": data.generated_at.isoformat(),
            "vehicles_to_send": [
                {
                    "incident_phase_id": str(item.incident_phase_id),
                    "vehicle_id": str(item.vehicle_id),
                    "distance_km": item.distance_km,
                    "estimated_time_min": item.estimated_time_min,
                    "energy_level": item.energy_level,
                    "score": item.score,
                    "rank": item.rank,
                }
                for item in data.vehicles_to_send
            ],
            "missing": [
                {
                    "incident_phase_id": str(item.incident_phase_id),
                    "vehicle_type_id": str(item.vehicle_type_id),
                    "missing_quantity": item.missing_quantity,
                }
                for item in data.missing
            ],
        }
