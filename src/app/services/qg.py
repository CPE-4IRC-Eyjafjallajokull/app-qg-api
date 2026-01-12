"""Service de gestion des opérations du QG (Quartier Général)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Incident,
    IncidentPhase,
    PhaseTypeVehicleRequirement,
    PhaseTypeVehicleRequirementGroup,
    Vehicle,
    VehicleAssignment,
    VehicleType,
)


class QGService:
    """Service pour les opérations du QG."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def get_incident_status(incident: Incident) -> str:
        """Détermine le statut d'un incident."""
        return "ENDED" if incident.ended_at else "ONGOING"

    async def fetch_requirement_groups(
        self, phase_type_ids: list[UUID]
    ) -> list[PhaseTypeVehicleRequirementGroup]:
        """Récupère les groupes de requirements pour les types de phase donnés."""
        if not phase_type_ids:
            return []

        groups_result = await self.session.execute(
            select(PhaseTypeVehicleRequirementGroup)
            .options(
                selectinload(PhaseTypeVehicleRequirementGroup.phase_type),
                selectinload(
                    PhaseTypeVehicleRequirementGroup.requirements
                ).selectinload(PhaseTypeVehicleRequirement.vehicle_type),
            )
            .where(PhaseTypeVehicleRequirementGroup.phase_type_id.in_(phase_type_ids))
        )

        groups = list(groups_result.scalars().all())
        return groups

    async def fetch_active_phases(self, incident_id: UUID) -> list[IncidentPhase]:
        """Récupère les phases actives d'un incident."""
        phases_result = await self.session.execute(
            select(IncidentPhase).where(
                IncidentPhase.incident_id == incident_id,
                IncidentPhase.ended_at.is_(None),
            )
        )
        return list(phases_result.scalars().all())

    async def fetch_active_assignments_by_phase(
        self, phase_ids: list[UUID]
    ) -> dict[UUID, dict[UUID, int]]:
        """Récupère les affectations actives par phase et type de véhicule."""
        if not phase_ids:
            return {}

        assignments_result = await self.session.execute(
            select(
                VehicleAssignment.incident_phase_id,
                Vehicle.vehicle_type_id,
                func.count(VehicleAssignment.vehicle_assignment_id),
            )
            .join(Vehicle, VehicleAssignment.vehicle_id == Vehicle.vehicle_id)
            .where(
                VehicleAssignment.incident_phase_id.in_(phase_ids),
                VehicleAssignment.unassigned_at.is_(None),
            )
            .group_by(
                VehicleAssignment.incident_phase_id,
                Vehicle.vehicle_type_id,
            )
        )

        assigned_by_phase: dict[UUID, dict[UUID, int]] = {}
        for phase_id, vehicle_type_id, count in assignments_result:
            phase_assignments = assigned_by_phase.setdefault(phase_id, {})
            phase_assignments[vehicle_type_id] = int(count)

        return assigned_by_phase

    @staticmethod
    def select_phase_by_type(phases: list[IncidentPhase]) -> dict[UUID, IncidentPhase]:
        """Sélectionne la phase active de priorité maximale par type."""
        selected: dict[UUID, IncidentPhase] = {}
        for phase in phases:
            current = selected.get(phase.phase_type_id)
            if current is None or (phase.priority or 0) > (current.priority or 0):
                selected[phase.phase_type_id] = phase
        return selected

    @staticmethod
    def aggregate_group_requirements(
        group: PhaseTypeVehicleRequirementGroup,
    ) -> dict[UUID, int]:
        """Agrège les requirements d'un groupe unique."""
        required_by_type: dict[UUID, int] = {}
        requirements = group.requirements
        group_total = 0
        for requirement in requirements:
            count = requirement.min_quantity or 0
            group_total += count
            if count:
                required_by_type[requirement.vehicle_type_id] = (
                    required_by_type.get(requirement.vehicle_type_id, 0) + count
                )

        target_total = group_total
        if group.min_total is not None:
            target_total = max(group_total, group.min_total)

        if group.max_total is not None:
            target_total = min(target_total, group.max_total)

        if target_total > group_total and requirements:
            sorted_requirements = sorted(
                requirements,
                key=lambda req: (
                    req.preference_rank is None,
                    req.preference_rank or 0,
                ),
            )
            remaining = target_total - group_total
            index = 0
            while remaining > 0:
                requirement = sorted_requirements[index % len(sorted_requirements)]
                required_by_type[requirement.vehicle_type_id] = (
                    required_by_type.get(requirement.vehicle_type_id, 0) + 1
                )
                remaining -= 1
                index += 1
        return required_by_type

    @staticmethod
    def aggregate_requirements(
        groups: list[PhaseTypeVehicleRequirementGroup],
    ) -> tuple[dict[UUID, int], dict[UUID, VehicleType]]:
        """
        Agrège les requirements de véhicules à partir des groupes.

        Retourne un tuple contenant :
        - Un dictionnaire {vehicle_type_id: quantité requise}
        - Un dictionnaire {vehicle_type_id: VehicleType}
        """
        required_by_type: dict[UUID, int] = {}
        vehicle_types: dict[UUID, VehicleType] = {}

        for group in groups:
            for requirement in group.requirements:
                vehicle_types[requirement.vehicle_type_id] = requirement.vehicle_type
            group_required = QGService.aggregate_group_requirements(group)
            for vehicle_type_id, count in group_required.items():
                required_by_type[vehicle_type_id] = (
                    required_by_type.get(vehicle_type_id, 0) + count
                )

        return required_by_type, vehicle_types

    @staticmethod
    def aggregate_requirements_by_phase(
        groups: list[PhaseTypeVehicleRequirementGroup],
    ) -> dict[UUID, dict[UUID, int]]:
        """Agrège les requirements par type de phase."""
        required_by_phase: dict[UUID, dict[UUID, int]] = {}
        for group in groups:
            if group.phase_type_id is None:
                continue
            group_required = QGService.aggregate_group_requirements(group)
            phase_requirements = required_by_phase.setdefault(group.phase_type_id, {})
            for vehicle_type_id, count in group_required.items():
                phase_requirements[vehicle_type_id] = (
                    phase_requirements.get(vehicle_type_id, 0) + count
                )
        return required_by_phase

    async def build_assignment_request(self, incident_id: UUID) -> list[dict]:
        """Construit la liste des véhicules requis par phase active."""
        phases = await self.fetch_active_phases(incident_id)
        selected_by_type = self.select_phase_by_type(phases)
        if not selected_by_type:
            return []
        ordered_phases = sorted(
            selected_by_type.values(),
            key=lambda phase: (phase.priority or 0),
            reverse=True,
        )
        return await self._build_assignment_request_for_phases(ordered_phases)

    async def build_assignment_request_for_phase(
        self, incident_phase: IncidentPhase
    ) -> list[dict]:
        """Construit la liste des véhicules requis pour une phase donnée."""
        return await self._build_assignment_request_for_phases([incident_phase])

    async def _build_assignment_request_for_phases(
        self, phases: list[IncidentPhase]
    ) -> list[dict]:
        active_phases = [phase for phase in phases if phase.ended_at is None]
        phase_type_ids = [phase.phase_type_id for phase in active_phases]
        if not phase_type_ids:
            return []
        groups = await self.fetch_requirement_groups(phase_type_ids)
        required_by_phase_type = self.aggregate_requirements_by_phase(groups)
        assigned_by_phase = await self.fetch_active_assignments_by_phase(
            [phase.incident_phase_id for phase in active_phases]
        )

        vehicles_needed: list[dict] = []
        for phase in active_phases:
            requirements = required_by_phase_type.get(phase.phase_type_id, {})
            assigned_by_type = assigned_by_phase.get(phase.incident_phase_id, {})
            for vehicle_type_id, quantity in requirements.items():
                missing_quantity = quantity - assigned_by_type.get(vehicle_type_id, 0)
                if missing_quantity <= 0:
                    continue
                vehicles_needed.append(
                    {
                        "vehicle_type_id": vehicle_type_id,
                        "quantity": missing_quantity,
                        "incident_phase_id": phase.incident_phase_id,
                    }
                )
        return vehicles_needed
