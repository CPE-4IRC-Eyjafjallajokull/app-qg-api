"""Service de gestion des opérations du QG (Quartier Général)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Incident,
    IncidentPhase,
    PhaseTypeVehicleRequirement,
    PhaseTypeVehicleRequirementGroup,
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

    async def get_active_phase_type_ids(self, incident_id: UUID) -> list[UUID]:
        """Récupère les IDs des types de phase actifs pour un incident."""
        phase_type_rows = await self.session.execute(
            select(IncidentPhase.phase_type_id)
            .where(
                IncidentPhase.incident_id == incident_id,
                IncidentPhase.ended_at.is_(None),
            )
            .distinct()
        )
        return [row[0] for row in phase_type_rows]

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
        return list(groups_result.scalars().all())

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
            requirements = group.requirements
            group_total = 0
            for requirement in requirements:
                vehicle_types[requirement.vehicle_type_id] = requirement.vehicle_type
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

        return required_by_type, vehicle_types
