from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from .vehicles import Vehicle, VehicleType


class VehicleConsumableType(Base):
    __tablename__ = "vehicle_consumable_types"

    vehicle_consumable_type_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    label: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    consumable_specs: Mapped[list["VehicleTypeConsumableSpec"]] = relationship(
        "VehicleTypeConsumableSpec",
        back_populates="consumable_type",
        passive_deletes=True,
    )
    stocks: Mapped[list["VehicleConsumableStock"]] = relationship(
        "VehicleConsumableStock",
        back_populates="consumable_type",
        passive_deletes=True,
    )


class VehicleTypeConsumableSpec(Base):
    __tablename__ = "vehicle_type_consumable_specs"
    __table_args__ = (
        Index("ix_vehicle_type_consumable_specs_vehicle_type", "vehicle_type_id"),
        Index("ix_vehicle_type_consumable_specs_consumable_type", "consumable_type_id"),
    )

    vehicle_type_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicle_types.vehicle_type_id", ondelete="CASCADE"),
        primary_key=True,
    )
    consumable_type_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "vehicle_consumable_types.vehicle_consumable_type_id", ondelete="CASCADE"
        ),
        primary_key=True,
    )
    capacity_qty: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    initial_qty: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    is_applicable: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    vehicle_type: Mapped["VehicleType"] = relationship(
        "VehicleType", back_populates="consumable_specs", passive_deletes=True
    )
    consumable_type: Mapped[VehicleConsumableType] = relationship(
        "VehicleConsumableType", back_populates="consumable_specs"
    )


class VehicleConsumableStock(Base):
    __tablename__ = "vehicle_consumables_stock"
    __table_args__ = (
        Index("ix_vehicle_consumables_stock_vehicle", "vehicle_id"),
        Index("ix_vehicle_consumables_stock_consumable_type", "consumable_type_id"),
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"),
        primary_key=True,
    )
    consumable_type_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "vehicle_consumable_types.vehicle_consumable_type_id", ondelete="CASCADE"
        ),
        primary_key=True,
    )
    current_qty: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    last_update: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    vehicle: Mapped["Vehicle"] = relationship(
        "Vehicle", back_populates="consumable_stocks", passive_deletes=True
    )
    consumable_type: Mapped[VehicleConsumableType] = relationship(
        "VehicleConsumableType", back_populates="stocks"
    )
