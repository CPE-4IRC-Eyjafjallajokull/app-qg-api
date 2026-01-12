from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DOUBLE_PRECISION,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    UniqueConstraint,
    desc,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from app.models.incidents import Incident, IncidentPhase
    from app.models.vehicles import Vehicle, VehicleType


class VehicleAssignmentProposal(Base):
    __tablename__ = "vehicle_assignment_proposals"
    __table_args__ = (
        CheckConstraint(
            "(validated_at IS NULL) OR (rejected_at IS NULL)",
            name="chk_vap_validation_xor",
        ),
        Index(
            "idx_vap_incident_generated_at",
            "incident_id",
            desc("generated_at"),
        ),
    )

    proposal_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("incidents.incident_id", ondelete="CASCADE"),
        nullable=False,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    validated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    incident: Mapped["Incident"] = relationship(
        "Incident", back_populates="assignment_proposals", passive_deletes=True
    )
    items: Mapped[list["VehicleAssignmentProposalItem"]] = relationship(
        "VehicleAssignmentProposalItem",
        back_populates="proposal",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    missing: Mapped[list["VehicleAssignmentProposalMissing"]] = relationship(
        "VehicleAssignmentProposalMissing",
        back_populates="proposal",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class VehicleAssignmentProposalItem(Base, CreatedAtMixin):
    __tablename__ = "vehicle_assignment_proposal_items"
    __table_args__ = (
        PrimaryKeyConstraint(
            "proposal_id",
            "incident_phase_id",
            "vehicle_id",
            name="pk_vehicle_assignment_proposal_items",
        ),
        UniqueConstraint(
            "proposal_id",
            "incident_phase_id",
            "proposal_rank",
            name="uq_vehicle_assignment_proposal_items_rank",
        ),
        CheckConstraint("distance_km >= 0", name="chk_vapi_distance_km_nonneg"),
        CheckConstraint(
            "estimated_time_min >= 0", name="chk_vapi_estimated_time_min_nonneg"
        ),
        CheckConstraint(
            "energy_level >= 0 AND energy_level <= 1",
            name="chk_vapi_energy_level_range",
        ),
        CheckConstraint(
            "score >= 0 AND score <= 1",
            name="chk_vapi_score_range",
        ),
        CheckConstraint(
            "(route_geometry ? 'type') AND (route_geometry ? 'coordinates') "
            "AND jsonb_typeof(route_geometry->'type') = 'string' "
            "AND jsonb_typeof(route_geometry->'coordinates') = 'array'",
            name="chk_vapi_route_geometry_shape",
        ),
        CheckConstraint(
            "route_geometry->>'type' = 'LineString'",
            name="chk_vapi_route_geometry_type",
        ),
        Index(
            "idx_vapi_phase_score",
            "incident_phase_id",
            desc("score"),
        ),
        Index("idx_vapi_vehicle", "vehicle_id"),
    )

    proposal_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicle_assignment_proposals.proposal_id", ondelete="CASCADE"),
        nullable=False,
    )
    incident_phase_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("incident_phases.incident_phase_id", ondelete="CASCADE"),
        nullable=False,
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicles.vehicle_id", ondelete="RESTRICT"),
        nullable=False,
    )
    proposal_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_km: Mapped[float] = mapped_column(DOUBLE_PRECISION, nullable=False)
    estimated_time_min: Mapped[int] = mapped_column(Integer, nullable=False)
    route_geometry: Mapped[dict] = mapped_column(JSONB, nullable=False)
    energy_level: Mapped[float] = mapped_column(Float, nullable=False)
    score: Mapped[float] = mapped_column(DOUBLE_PRECISION, nullable=False)
    proposal: Mapped[VehicleAssignmentProposal] = relationship(
        "VehicleAssignmentProposal", back_populates="items"
    )
    incident_phase: Mapped["IncidentPhase"] = relationship(
        "IncidentPhase",
        back_populates="assignment_proposal_items",
        passive_deletes=True,
    )
    vehicle: Mapped["Vehicle"] = relationship(
        "Vehicle", back_populates="assignment_proposal_items", passive_deletes=True
    )


class VehicleAssignmentProposalMissing(Base, CreatedAtMixin):
    __tablename__ = "vehicle_assignment_proposal_missing"
    __table_args__ = (
        PrimaryKeyConstraint(
            "proposal_id",
            "incident_phase_id",
            "vehicle_type_id",
            name="pk_vehicle_assignment_proposal_missing",
        ),
        CheckConstraint(
            "missing_quantity >= 0", name="chk_vapm_missing_quantity_nonneg"
        ),
        Index("idx_vapm_proposal", "proposal_id"),
    )

    proposal_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicle_assignment_proposals.proposal_id", ondelete="CASCADE"),
        nullable=False,
    )
    incident_phase_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("incident_phases.incident_phase_id", ondelete="CASCADE"),
        nullable=False,
    )
    vehicle_type_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicle_types.vehicle_type_id", ondelete="RESTRICT"),
        nullable=False,
    )
    missing_quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    proposal: Mapped[VehicleAssignmentProposal] = relationship(
        "VehicleAssignmentProposal", back_populates="missing"
    )
    incident_phase: Mapped["IncidentPhase"] = relationship(
        "IncidentPhase",
        back_populates="assignment_proposal_missing",
        passive_deletes=True,
    )
    vehicle_type: Mapped["VehicleType"] = relationship(
        "VehicleType",
        back_populates="assignment_proposal_missing",
        passive_deletes=True,
    )
