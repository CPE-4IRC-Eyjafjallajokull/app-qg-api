from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger
from app.models import (
    Incident,
    VehicleAssignmentProposal,
    VehicleAssignmentProposalItem,
    VehicleAssignmentProposalMissing,
)
from app.schemas.routing.route import LineStringGeometry
from app.services.db.postgres import PostgresManager
from app.services.events import Event, SSEManager
from app.services.messaging.queues import Queue, subscription_queues
from app.services.messaging.rabbitmq import RabbitMQManager
from app.services.messaging.subscriber import (
    QueueEvent,
    RabbitMQSubscriptionService,
)

log = get_logger(__name__)


# --- Pydantic schemas for RabbitMQ message parsing ---


class ProposalItemMessage(BaseModel):
    incident_phase_id: UUID
    vehicle_id: UUID
    distance_km: float = Field(ge=0)
    estimated_time_min: float = Field(ge=0)
    route_geometry: LineStringGeometry
    energy_level: float = Field(ge=0, le=1)
    score: float = Field(ge=0, le=1)
    rationale: str | None = None


class ProposalMessage(BaseModel):
    proposal_id: UUID
    incident_id: UUID
    generated_at: datetime
    proposals: list[ProposalItemMessage] = []
    missing_by_vehicle_type: dict[UUID, int] = {}


class ApplicationSubscriptions(RabbitMQSubscriptionService):
    """Application-specific event handlers wired on top of the base subscriber."""

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

        # Register event handlers once at init time
        self.on(
            Event.VEHICLE_ASSIGNMENT_PROPOSAL.value,
            self._handle_vehicle_assignment_proposal,
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
        await self._sse_manager.notify(
            Event.VEHICLE_ASSIGNMENT_PROPOSAL.value, sse_payload
        )
        log.info(
            "subscription.event.forwarded",
            queue=message.queue,
            event_name=Event.VEHICLE_ASSIGNMENT_PROPOSAL.value,
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

            # Create items with rank per phase
            phase_ranks: dict[UUID, int] = {}
            for item in data.proposals:
                phase_ranks[item.incident_phase_id] = (
                    phase_ranks.get(item.incident_phase_id, 0) + 1
                )
                session.add(
                    VehicleAssignmentProposalItem(
                        proposal_id=data.proposal_id,
                        incident_phase_id=item.incident_phase_id,
                        vehicle_id=item.vehicle_id,
                        proposal_rank=phase_ranks[item.incident_phase_id],
                        distance_km=item.distance_km,
                        estimated_time_min=int(item.estimated_time_min),
                        route_geometry=item.route_geometry.model_dump(),
                        energy_level=item.energy_level,
                        score=item.score,
                        rationale=item.rationale,
                    )
                )

            # Create missing entries (use single phase from proposals if available)
            # Skip if no phase_id can be determined (PK requires non-null incident_phase_id)
            phase_id = self._infer_phase_id(data.proposals)
            if phase_id is not None:
                for vehicle_type_id, quantity in data.missing_by_vehicle_type.items():
                    session.add(
                        VehicleAssignmentProposalMissing(
                            proposal_id=data.proposal_id,
                            incident_phase_id=phase_id,
                            vehicle_type_id=vehicle_type_id,
                            missing_quantity=quantity,
                        )
                    )
            elif data.missing_by_vehicle_type:
                log.warning(
                    "subscription.assignment_proposal.missing_skipped",
                    proposal_id=data.proposal_id,
                    reason="no_single_phase_id",
                    missing_count=len(data.missing_by_vehicle_type),
                )

            try:
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
            items=len(data.proposals),
            missing=len(data.missing_by_vehicle_type),
        )

    @staticmethod
    def _infer_phase_id(proposals: list[ProposalItemMessage]) -> UUID | None:
        """Return phase_id if all proposals have the same one, else None."""
        if not proposals:
            return None
        phase_ids = {p.incident_phase_id for p in proposals}
        return next(iter(phase_ids)) if len(phase_ids) == 1 else None

    @staticmethod
    def _build_sse_payload(data: ProposalMessage) -> dict:
        """Build SSE payload without route_geometry."""
        return {
            "proposal_id": str(data.proposal_id),
            "incident_id": str(data.incident_id),
            "generated_at": data.generated_at.isoformat(),
            "proposals": [
                {
                    "incident_phase_id": str(item.incident_phase_id),
                    "vehicle_id": str(item.vehicle_id),
                    "distance_km": item.distance_km,
                    "estimated_time_min": item.estimated_time_min,
                    "energy_level": item.energy_level,
                    "score": item.score,
                    "rationale": item.rationale,
                }
                for item in data.proposals
            ],
            "missing_by_vehicle_type": {
                str(k): v for k, v in data.missing_by_vehicle_type.items()
            },
        }
