from uuid import UUID

from pydantic import BaseModel, ConfigDict


class QGVehicleTypeRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_type_id: UUID
    code: str
    label: str | None = None


class QGPhaseTypeRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase_type_id: UUID
    code: str
    label: str | None = None


class QGVehicleSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: UUID
    immatriculation: str
    vehicle_type: QGVehicleTypeRef
