from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from geoalchemy2 import Geography
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from .vehicles import Vehicle


class InterestPoint(Base):
    __tablename__ = "interest_points"
    __table_args__ = (Index("ix_interest_points_city_zipcode", "city", "zipcode"),)

    interest_point_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    zipcode: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    interest_point_kind_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interest_point_kinds.interest_point_kind_id", ondelete="SET NULL"),
        nullable=True,
    )

    kind: Mapped[Optional["InterestPointKind"]] = relationship(
        "InterestPointKind", back_populates="interest_points"
    )
    vehicles_based_here: Mapped[list["Vehicle"]] = relationship(
        "Vehicle",
        back_populates="base_interest_point",
        passive_deletes=True,
    )
    consumables: Mapped[list["InterestPointConsumable"]] = relationship(
        "InterestPointConsumable",
        back_populates="interest_point",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class InterestPointKind(Base):
    __tablename__ = "interest_point_kinds"

    interest_point_kind_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    label: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    interest_points: Mapped[list[InterestPoint]] = relationship(
        "InterestPoint", back_populates="kind", passive_deletes=True
    )


class InterestPointConsumableType(Base):
    __tablename__ = "interest_point_consumable_types"

    interest_point_consumable_type_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    label: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    interest_point_consumables: Mapped[list["InterestPointConsumable"]] = relationship(
        "InterestPointConsumable",
        back_populates="consumable_type",
        passive_deletes=True,
    )


class InterestPointConsumable(Base):
    __tablename__ = "interest_point_consumables"
    __table_args__ = (
        Index("ix_interest_point_consumables_point", "interest_point_id"),
        Index(
            "ix_interest_point_consumables_consumable_type",
            "interest_point_consumable_type_id",
        ),
    )

    interest_point_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interest_points.interest_point_id", ondelete="CASCADE"),
        primary_key=True,
    )
    interest_point_consumable_type_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "interest_point_consumable_types.interest_point_consumable_type_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    current_qty: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    last_update: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    interest_point: Mapped[InterestPoint] = relationship(
        "InterestPoint", back_populates="consumables", passive_deletes=True
    )
    consumable_type: Mapped[InterestPointConsumableType] = relationship(
        "InterestPointConsumableType", back_populates="interest_point_consumables"
    )
