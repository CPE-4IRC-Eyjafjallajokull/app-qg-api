from app.models.assignment_proposals import (
    VehicleAssignmentProposal,
    VehicleAssignmentProposalItem,
    VehicleAssignmentProposalMissing,
)
from app.models.assignment_requests import VehicleAssignmentRequest
from app.models.base import Base, CreatedAtMixin, TimestampMixin
from app.models.casualties import (
    Casualty,
    CasualtyStatus,
    CasualtyTransport,
    CasualtyType,
)
from app.models.consumables import (
    VehicleConsumableStock,
    VehicleConsumableType,
    VehicleTypeConsumableSpec,
)
from app.models.enums import IncidentPhaseDependencyKind, VehicleRequirementRule
from app.models.incidents import (
    Incident,
    IncidentPhase,
    IncidentPhaseDependency,
    PhaseCategory,
    PhaseType,
    PhaseTypeVehicleRequirement,
    PhaseTypeVehicleRequirementGroup,
    Reinforcement,
    ReinforcementVehicleRequest,
)
from app.models.interest_points import (
    InterestPoint,
    InterestPointConsumable,
    InterestPointConsumableType,
    InterestPointKind,
)
from app.models.operators import Operator
from app.models.vehicles import (
    Energy,
    Vehicle,
    VehicleAssignment,
    VehiclePositionLog,
    VehicleStatus,
    VehicleType,
)

__all__ = [
    "Base",
    "CreatedAtMixin",
    "TimestampMixin",
    "VehicleAssignmentProposal",
    "VehicleAssignmentProposalItem",
    "VehicleAssignmentProposalMissing",
    "VehicleAssignmentRequest",
    "Casualty",
    "CasualtyStatus",
    "CasualtyTransport",
    "CasualtyType",
    "Energy",
    "Incident",
    "IncidentPhase",
    "IncidentPhaseDependency",
    "IncidentPhaseDependencyKind",
    "InterestPoint",
    "InterestPointConsumable",
    "InterestPointConsumableType",
    "InterestPointKind",
    "Operator",
    "PhaseCategory",
    "PhaseType",
    "PhaseTypeVehicleRequirement",
    "PhaseTypeVehicleRequirementGroup",
    "Reinforcement",
    "ReinforcementVehicleRequest",
    "Vehicle",
    "VehicleAssignment",
    "VehicleConsumableStock",
    "VehicleConsumableType",
    "VehiclePositionLog",
    "VehicleRequirementRule",
    "VehicleStatus",
    "VehicleType",
    "VehicleTypeConsumableSpec",
]
