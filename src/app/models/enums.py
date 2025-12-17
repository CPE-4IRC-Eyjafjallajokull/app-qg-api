import enum


class IncidentPhaseDependencyKind(str, enum.Enum):
    CAUSE = "CAUSE"
    SEQUENCE = "SEQUENCE"
    RELATED = "RELATED"


class VehicleRequirementRule(str, enum.Enum):
    ALL = "ALL"
    ANY = "ANY"
