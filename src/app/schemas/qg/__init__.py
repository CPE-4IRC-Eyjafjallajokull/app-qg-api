from app.schemas.qg.assignment_proposals import (
    QGAssignmentProposalRead,
    QGAssignmentProposalsListRead,
    QGProposalItem,
    QGRejectProposalResponse,
    QGValidateProposalResponse,
)
from app.schemas.qg.casualties import (
    QGCasualtiesRead,
    QGCasualtyDetail,
    QGCasualtyStats,
)
from app.schemas.qg.common import (
    QGIncidentPhaseRef,
    QGPhaseTypeRef,
    QGVehicleSummary,
    QGVehicleTypeRef,
)
from app.schemas.qg.engagements import (
    QGIncidentEngagementsRead,
    QGVehicleAssignmentDetail,
)
from app.schemas.qg.incidents import QGIncidentPhaseCreate, QGIncidentRead
from app.schemas.qg.resource_planning import QGResourcePlanningRead
from app.schemas.qg.situation import QGIncidentSituationRead
from app.schemas.qg.vehicles import (
    QGVehicleAssignRequest,
    QGVehicleDetail,
    QGVehiclePosition,
    QGVehiclePositionRead,
    QGVehiclesListRead,
)

__all__ = [
    "QGAssignmentProposalRead",
    "QGAssignmentProposalsListRead",
    "QGProposalItem",
    "QGRejectProposalResponse",
    "QGValidateProposalResponse",
    "QGCasualtiesRead",
    "QGCasualtyDetail",
    "QGCasualtyStats",
    "QGIncidentPhaseRef",
    "QGPhaseTypeRef",
    "QGVehicleSummary",
    "QGVehicleTypeRef",
    "QGIncidentEngagementsRead",
    "QGVehicleAssignmentDetail",
    "QGResourcePlanningRead",
    "QGIncidentSituationRead",
    "QGVehicleDetail",
    "QGVehiclesListRead",
    "QGVehiclePosition",
    "QGVehiclePositionRead",
    "QGVehicleAssignRequest",
    "QGIncidentPhaseCreate",
    "QGIncidentRead",
]
