from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DOUBLE_PRECISION,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from .assignment_proposals import (
        VehicleAssignmentProposalItem,
        VehicleAssignmentProposalMissing,
    )
    from .casualties import CasualtyTransport
    from .consumables import VehicleConsumableStock, VehicleTypeConsumableSpec
    from .incidents import (
        IncidentPhase,
        PhaseTypeVehicleRequirement,
        Reinforcement,
        ReinforcementVehicleRequest,
    )
    from .interest_points import InterestPoint
    from .operators import Operator
    from .vehicles import VehicleAssignment, VehicleType


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        Index("ix_vehicles_vehicle_type", "vehicle_type_id"),
        Index("ix_vehicles_status", "status_id"),
        Index("ix_vehicles_base_interest_point", "base_interest_point_id"),
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    vehicle_type_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicle_types.vehicle_type_id", ondelete="CASCADE"),
        nullable=False,
    )
    immatriculation: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True
    )
    energy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("energies.energy_id", ondelete="SET NULL"),
        nullable=True,
    )
    energy_level: Mapped[Optional[float]] = mapped_column(
        DOUBLE_PRECISION, nullable=True
    )
    base_interest_point_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interest_points.interest_point_id", ondelete="SET NULL"),
        nullable=True,
    )
    status_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicle_status.vehicle_status_id", ondelete="SET NULL"),
        nullable=True,
    )

    vehicle_type: Mapped["VehicleType"] = relationship(
        "VehicleType", back_populates="vehicles"
    )
    energy: Mapped[Optional["Energy"]] = relationship(
        "Energy", back_populates="vehicles"
    )
    base_interest_point: Mapped[Optional["InterestPoint"]] = relationship(
        "InterestPoint", back_populates="vehicles_based_here"
    )
    status: Mapped[Optional["VehicleStatus"]] = relationship(
        "VehicleStatus", back_populates="vehicles"
    )
    assignments: Mapped[list["VehicleAssignment"]] = relationship(
        "VehicleAssignment",
        back_populates="vehicle",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    position_logs: Mapped[list["VehiclePositionLog"]] = relationship(
        "VehiclePositionLog",
        back_populates="vehicle",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    assignment_proposal_items: Mapped[list["VehicleAssignmentProposalItem"]] = (
        relationship(
            "VehicleAssignmentProposalItem",
            back_populates="vehicle",
            passive_deletes=True,
        )
    )
    consumable_stocks: Mapped[list["VehicleConsumableStock"]] = relationship(
        "VehicleConsumableStock",
        back_populates="vehicle",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Energy(Base):
    __tablename__ = "energies"

    energy_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    label: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    vehicles: Mapped[list[Vehicle]] = relationship(
        "Vehicle", back_populates="energy", passive_deletes=True
    )


class VehicleType(Base):
    __tablename__ = "vehicle_types"

    vehicle_type_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    vehicles: Mapped[list[Vehicle]] = relationship(
        "Vehicle", back_populates="vehicle_type", passive_deletes=True
    )
    consumable_specs: Mapped[list["VehicleTypeConsumableSpec"]] = relationship(
        "VehicleTypeConsumableSpec",
        back_populates="vehicle_type",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    requirement_entries: Mapped[list["PhaseTypeVehicleRequirement"]] = relationship(
        "PhaseTypeVehicleRequirement",
        back_populates="vehicle_type",
        passive_deletes=True,
    )
    assignment_proposal_missing: Mapped[list["VehicleAssignmentProposalMissing"]] = (
        relationship(
            "VehicleAssignmentProposalMissing",
            back_populates="vehicle_type",
            passive_deletes=True,
        )
    )
    reinforcement_requests: Mapped[list["ReinforcementVehicleRequest"]] = relationship(
        "ReinforcementVehicleRequest",
        back_populates="vehicle_type",
        passive_deletes=True,
    )


class VehicleStatus(Base):
    __tablename__ = "vehicle_status"

    vehicle_status_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    label: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    vehicles: Mapped[list[Vehicle]] = relationship(
        "Vehicle", back_populates="status", passive_deletes=True
    )


class VehicleAssignment(Base):
    __tablename__ = "vehicle_assignments"
    __table_args__ = (
        Index("ix_vehicle_assignments_vehicle", "vehicle_id"),
        Index("ix_vehicle_assignments_incident_phase", "incident_phase_id"),
        Index("ix_vehicle_assignments_reinforcement", "reinforcement_id"),
        Index(
            "uq_vehicle_active_assignment",
            "vehicle_id",
            unique=True,
            postgresql_where=text("unassigned_at IS NULL"),
        ),
    )

    vehicle_assignment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"),
        nullable=False,
    )
    incident_phase_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("incident_phases.incident_phase_id", ondelete="SET NULL"),
        nullable=True,
    )
    reinforcement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("reinforcements.reinforcement_id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    arrived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    assigned_by_operator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("operators.operator_id", ondelete="SET NULL"),
        nullable=True,
    )
    validated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    validated_by_operator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("operators.operator_id", ondelete="SET NULL"),
        nullable=True,
    )
    unassigned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    vehicle: Mapped[Vehicle] = relationship(
        "Vehicle", back_populates="assignments", passive_deletes=True
    )
    incident_phase: Mapped[Optional["IncidentPhase"]] = relationship(
        "IncidentPhase", back_populates="vehicle_assignments", passive_deletes=True
    )
    reinforcement: Mapped[Optional["Reinforcement"]] = relationship(
        "Reinforcement", back_populates="vehicle_assignments", passive_deletes=True
    )
    assigned_by_operator: Mapped[Optional["Operator"]] = relationship(
        "Operator",
        foreign_keys=[assigned_by_operator_id],
        back_populates="vehicle_assignments_made",
    )
    validated_by_operator: Mapped[Optional["Operator"]] = relationship(
        "Operator", foreign_keys=[validated_by_operator_id]
    )
    casualty_transports: Mapped[list["CasualtyTransport"]] = relationship(
        "CasualtyTransport",
        back_populates="vehicle_assignment",
        passive_deletes=True,
    )


class VehiclePositionLog(Base):
    __tablename__ = "vehicle_position_logs"
    __table_args__ = (
        Index("ix_vehicle_position_logs_vehicle_timestamp", "vehicle_id", "timestamp"),
    )

    vehicle_position_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"),
        nullable=False,
    )
    latitude: Mapped[Optional[float]] = mapped_column(DOUBLE_PRECISION, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(DOUBLE_PRECISION, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    vehicle: Mapped[Vehicle] = relationship(
        "Vehicle", back_populates="position_logs", passive_deletes=True
    )
