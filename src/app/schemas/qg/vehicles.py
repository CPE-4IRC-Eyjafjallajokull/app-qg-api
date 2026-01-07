from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class QGEnergyRef(BaseModel):
    """Référence légère vers un type d'énergie."""

    model_config = ConfigDict(extra="forbid")

    energy_id: UUID
    label: str


class QGVehicleStatusRef(BaseModel):
    """Référence légère vers un statut de véhicule."""

    model_config = ConfigDict(extra="forbid")

    vehicle_status_id: UUID
    label: str


class QGVehicleTypeDetail(BaseModel):
    """Détail complet d'un type de véhicule."""

    model_config = ConfigDict(extra="forbid")

    vehicle_type_id: UUID
    code: str
    label: str


class QGBaseInterestPoint(BaseModel):
    """Point d'intérêt de base du véhicule (caserne, etc.)."""

    model_config = ConfigDict(extra="forbid")

    interest_point_id: UUID
    name: str | None = None
    address: str | None = None
    zipcode: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class QGConsumableTypeRef(BaseModel):
    """Référence vers un type de consommable."""

    model_config = ConfigDict(extra="forbid")

    vehicle_consumable_type_id: UUID
    label: str
    unit: str | None = None


class QGVehicleConsumableStock(BaseModel):
    """Stock d'un consommable pour un véhicule."""

    model_config = ConfigDict(extra="forbid")

    consumable_type: QGConsumableTypeRef
    current_quantity: Decimal | None = None
    last_update: datetime


class QGVehiclePosition(BaseModel):
    """Position actuelle d'un véhicule."""

    model_config = ConfigDict(extra="forbid")

    latitude: float | None = None
    longitude: float | None = None
    timestamp: datetime


class QGVehiclePositionRead(BaseModel):
    """Lecture de la position actuelle d'un véhicule."""

    model_config = ConfigDict(extra="forbid")

    vehicle_immatriculation: str
    latitude: float | None = None
    longitude: float | None = None
    timestamp: datetime


class QGVehicleStatusUpdate(BaseModel):
    """Mise à jour du statut d'un véhicule."""

    model_config = ConfigDict(extra="forbid")

    status_label: str
    timestamp: datetime


class QGVehicleStatusRead(BaseModel):
    """Lecture du statut actuel d'un véhicule."""

    model_config = ConfigDict(extra="forbid")

    vehicle_immatriculation: str
    status_label: str
    timestamp: datetime


class QGActiveAssignment(BaseModel):
    """Affectation active d'un véhicule."""

    model_config = ConfigDict(extra="forbid")

    vehicle_assignment_id: UUID
    incident_phase_id: UUID | None = None
    assigned_at: datetime
    assigned_by_operator_id: UUID | None = None


class QGVehicleDetail(BaseModel):
    """Détail complet d'un véhicule pour le QG."""

    model_config = ConfigDict(extra="forbid")

    vehicle_id: UUID
    immatriculation: str
    vehicle_type: QGVehicleTypeDetail
    energy: QGEnergyRef | None = None
    energy_level: float | None = None
    status: QGVehicleStatusRef | None = None
    base_interest_point: QGBaseInterestPoint | None = None
    current_position: QGVehiclePosition | None = None
    consumable_stocks: list[QGVehicleConsumableStock]
    active_assignment: QGActiveAssignment | None = None


class QGVehiclesListRead(BaseModel):
    """Réponse de la liste des véhicules pour le QG."""

    model_config = ConfigDict(extra="forbid")

    vehicles: list[QGVehicleDetail]
    total: int
