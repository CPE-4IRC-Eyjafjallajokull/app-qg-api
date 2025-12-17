from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, TimestampMixin
from app.models.enums import IncidentPhaseDependencyKind, VehicleRequirementRule

if TYPE_CHECKING:
    from .casualties import Casualty
    from .interventions import Intervention
    from .operators import Operator
    from .vehicles import VehicleAssignment, VehicleType


class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"
    __table_args__ = (
        Index("ix_incidents_created_by", "created_by_operator_id"),
        Index("ix_incidents_city_zipcode", "city", "zipcode"),
        Index("ix_incidents_created_at", "created_at"),
    )

    incident_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_by_operator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("operators.operator_id", ondelete="SET NULL"),
        nullable=True,
    )
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    zipcode: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    location: Mapped[Optional[str]] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_by: Mapped[Optional["Operator"]] = relationship(
        "Operator", back_populates="incidents_created"
    )
    phases: Mapped[list["IncidentPhase"]] = relationship(
        "IncidentPhase",
        back_populates="incident",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    interventions: Mapped[list["Intervention"]] = relationship(
        "Intervention",
        back_populates="incident",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PhaseCategory(Base):
    __tablename__ = "phase_categories"

    phase_category_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    label: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    phase_types: Mapped[list["PhaseType"]] = relationship(
        "PhaseType",
        back_populates="category",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PhaseType(Base):
    __tablename__ = "phase_types"
    __table_args__ = (
        Index("ix_phase_types_category", "phase_category_id"),
        Index("ix_phase_types_code", "code", unique=True),
    )

    phase_type_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    phase_category_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("phase_categories.phase_category_id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    label: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    default_criticality: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    category: Mapped[PhaseCategory] = relationship(
        "PhaseCategory", back_populates="phase_types"
    )
    incident_phases: Mapped[list["IncidentPhase"]] = relationship(
        "IncidentPhase",
        back_populates="phase_type",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    vehicle_requirement_groups: Mapped[list["PhaseTypeVehicleRequirementGroup"]] = (
        relationship(
            "PhaseTypeVehicleRequirementGroup",
            back_populates="phase_type",
            cascade="all, delete-orphan",
            passive_deletes=True,
        )
    )


class IncidentPhase(Base):
    __tablename__ = "incident_phases"
    __table_args__ = (
        Index("ix_incident_phases_incident", "incident_id"),
        Index("ix_incident_phases_phase_type", "phase_type_id"),
        Index("ix_incident_phases_priority", "priority"),
    )

    incident_phase_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("incidents.incident_id", ondelete="CASCADE"),
        nullable=False,
    )
    phase_type_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("phase_types.phase_type_id", ondelete="CASCADE"),
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    incident: Mapped[Incident] = relationship(
        "Incident", back_populates="phases", passive_deletes=True
    )
    phase_type: Mapped[PhaseType] = relationship(
        "PhaseType", back_populates="incident_phases"
    )
    dependencies: Mapped[list["IncidentPhaseDependency"]] = relationship(
        "IncidentPhaseDependency",
        back_populates="incident_phase",
        foreign_keys="IncidentPhaseDependency.incident_phase_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    dependents: Mapped[list["IncidentPhaseDependency"]] = relationship(
        "IncidentPhaseDependency",
        back_populates="depends_on_incident_phase",
        foreign_keys="IncidentPhaseDependency.depends_on_incident_phase_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    casualties: Mapped[list["Casualty"]] = relationship(
        "Casualty",
        back_populates="incident_phase",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    vehicle_assignments: Mapped[list["VehicleAssignment"]] = relationship(
        "VehicleAssignment",
        back_populates="incident_phase",
        passive_deletes=True,
    )


class IncidentPhaseDependency(Base, CreatedAtMixin):
    __tablename__ = "incident_phase_dependencies"
    __table_args__ = (
        Index("ix_incident_phase_dependencies_incident_phase", "incident_phase_id"),
        Index(
            "ix_incident_phase_dependencies_depends_on", "depends_on_incident_phase_id"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    incident_phase_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("incident_phases.incident_phase_id", ondelete="CASCADE"),
        nullable=False,
    )
    depends_on_incident_phase_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("incident_phases.incident_phase_id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[IncidentPhaseDependencyKind] = mapped_column(
        Enum(
            IncidentPhaseDependencyKind,
            name="incident_phase_dependency_kind",
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    incident_phase: Mapped[IncidentPhase] = relationship(
        "IncidentPhase",
        back_populates="dependencies",
        foreign_keys=[incident_phase_id],
        passive_deletes=True,
    )
    depends_on_incident_phase: Mapped[IncidentPhase] = relationship(
        "IncidentPhase",
        back_populates="dependents",
        foreign_keys=[depends_on_incident_phase_id],
        passive_deletes=True,
    )


class PhaseTypeVehicleRequirementGroup(Base, CreatedAtMixin):
    __tablename__ = "phase_type_vehicle_requirement_groups"
    __table_args__ = (
        Index("ix_phase_type_vehicle_requirement_groups_phase_type", "phase_type_id"),
        Index("ix_phase_type_vehicle_requirement_groups_priority", "priority"),
    )

    group_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    phase_type_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("phase_types.phase_type_id", ondelete="CASCADE"),
        nullable=False,
    )
    label: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rule: Mapped[VehicleRequirementRule] = mapped_column(
        Enum(
            VehicleRequirementRule,
            name="phase_type_vehicle_requirement_rule",
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    min_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    priority: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    is_hard: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    phase_type: Mapped[PhaseType] = relationship(
        "PhaseType", back_populates="vehicle_requirement_groups", passive_deletes=True
    )
    requirements: Mapped[list["PhaseTypeVehicleRequirement"]] = relationship(
        "PhaseTypeVehicleRequirement",
        back_populates="group",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PhaseTypeVehicleRequirement(Base, CreatedAtMixin):
    __tablename__ = "phase_type_vehicle_requirements"
    __table_args__ = (
        Index("ix_phase_type_vehicle_requirements_group", "group_id"),
        Index("ix_phase_type_vehicle_requirements_vehicle_type", "vehicle_type_id"),
    )

    group_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "phase_type_vehicle_requirement_groups.group_id", ondelete="CASCADE"
        ),
        primary_key=True,
    )
    vehicle_type_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicle_types.vehicle_type_id", ondelete="CASCADE"),
        primary_key=True,
    )
    min_qty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_qty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mandatory: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    preference_rank: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)

    group: Mapped[PhaseTypeVehicleRequirementGroup] = relationship(
        "PhaseTypeVehicleRequirementGroup",
        back_populates="requirements",
        passive_deletes=True,
    )
    vehicle_type: Mapped["VehicleType"] = relationship(
        "VehicleType", back_populates="requirement_entries"
    )
