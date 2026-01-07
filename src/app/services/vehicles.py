from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Vehicle,
    VehicleConsumableStock,
    VehiclePositionLog,
    VehicleStatus,
)
from app.schemas.qg.vehicles import (
    QGActiveAssignment,
    QGBaseInterestPoint,
    QGConsumableTypeRef,
    QGEnergyRef,
    QGVehicleConsumableStock,
    QGVehicleDetail,
    QGVehiclePosition,
    QGVehicleStatusRef,
    QGVehicleTypeDetail,
)


class VehicleService:
    """Service pour les opérations liées aux véhicules."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def fetch_all_vehicles_with_relations(self) -> list[Vehicle]:
        """Récupère tous les véhicules avec leurs relations nécessaires."""
        result = await self.session.execute(
            select(Vehicle)
            .options(
                selectinload(Vehicle.vehicle_type),
                selectinload(Vehicle.energy),
                selectinload(Vehicle.status),
                selectinload(Vehicle.base_interest_point),
                selectinload(Vehicle.consumable_stocks).selectinload(
                    VehicleConsumableStock.consumable_type
                ),
                selectinload(Vehicle.assignments),
            )
            .order_by(Vehicle.immatriculation)
        )
        return list(result.scalars().all())

    async def fetch_latest_positions(
        self, vehicle_ids: list[UUID]
    ) -> dict[UUID, VehiclePositionLog]:
        """Récupère la dernière position connue pour chaque véhicule."""
        if not vehicle_ids:
            return {}

        # Sous-requête pour obtenir le timestamp max par véhicule
        subquery = (
            select(
                VehiclePositionLog.vehicle_id,
                func.max(VehiclePositionLog.timestamp).label("max_timestamp"),
            )
            .where(VehiclePositionLog.vehicle_id.in_(vehicle_ids))
            .group_by(VehiclePositionLog.vehicle_id)
            .subquery()
        )

        # Requête principale pour récupérer les logs correspondants
        result = await self.session.execute(
            select(VehiclePositionLog).join(
                subquery,
                (VehiclePositionLog.vehicle_id == subquery.c.vehicle_id)
                & (VehiclePositionLog.timestamp == subquery.c.max_timestamp),
            )
        )

        return {log.vehicle_id: log for log in result.scalars().all()}

    @staticmethod
    def build_vehicle_detail(
        vehicle: Vehicle,
        latest_position: VehiclePositionLog | None,
    ) -> QGVehicleDetail:
        """Construit le DTO QGVehicleDetail à partir d'un véhicule."""
        # Type de véhicule
        vehicle_type = vehicle.vehicle_type
        vehicle_type_dto = QGVehicleTypeDetail(
            vehicle_type_id=vehicle_type.vehicle_type_id,
            code=vehicle_type.code,
            label=vehicle_type.label,
        )

        # Énergie
        energy_dto = None
        if vehicle.energy:
            energy_dto = QGEnergyRef(
                energy_id=vehicle.energy.energy_id,
                label=vehicle.energy.label,
            )

        # Statut
        status_dto = None
        if vehicle.status:
            status_dto = QGVehicleStatusRef(
                vehicle_status_id=vehicle.status.vehicle_status_id,
                label=vehicle.status.label,
            )

        # Point d'intérêt de base
        base_interest_point_dto = None
        if vehicle.base_interest_point:
            base_ip = vehicle.base_interest_point
            base_interest_point_dto = QGBaseInterestPoint(
                interest_point_id=base_ip.interest_point_id,
                name=base_ip.name,
                address=base_ip.address,
                zipcode=base_ip.zipcode,
                city=base_ip.city,
                latitude=base_ip.latitude,
                longitude=base_ip.longitude,
            )

        # Position actuelle
        current_position_dto = None
        if latest_position:
            current_position_dto = QGVehiclePosition(
                latitude=latest_position.latitude,
                longitude=latest_position.longitude,
                timestamp=latest_position.timestamp,
            )

        # Stocks de consommables
        consumable_stocks_dto = [
            QGVehicleConsumableStock(
                consumable_type=QGConsumableTypeRef(
                    vehicle_consumable_type_id=stock.consumable_type.vehicle_consumable_type_id,
                    label=stock.consumable_type.label,
                    unit=stock.consumable_type.unit,
                ),
                current_quantity=stock.current_quantity,
                last_update=stock.last_update,
            )
            for stock in vehicle.consumable_stocks
            if stock.consumable_type
        ]

        # Affectation active
        active_assignment_dto = None
        for assignment in vehicle.assignments:
            if assignment.unassigned_at is None:
                active_assignment_dto = QGActiveAssignment(
                    vehicle_assignment_id=assignment.vehicle_assignment_id,
                    incident_phase_id=assignment.incident_phase_id,
                    assigned_at=assignment.assigned_at,
                    assigned_by_operator_id=assignment.assigned_by_operator_id,
                )
                break

        return QGVehicleDetail(
            vehicle_id=vehicle.vehicle_id,
            immatriculation=vehicle.immatriculation,
            vehicle_type=vehicle_type_dto,
            energy=energy_dto,
            energy_level=vehicle.energy_level,
            status=status_dto,
            base_interest_point=base_interest_point_dto,
            current_position=current_position_dto,
            consumable_stocks=consumable_stocks_dto,
            active_assignment=active_assignment_dto,
        )

    async def create_vehicle_position(
        self,
        vehicle_id: UUID,
        latitude: float | None,
        longitude: float | None,
        timestamp: datetime,
    ) -> VehiclePositionLog:
        """Crée une nouvelle entrée de position pour un véhicule."""
        position = VehiclePositionLog(
            vehicle_id=vehicle_id,
            latitude=latitude,
            longitude=longitude,
            timestamp=timestamp,
        )
        self.session.add(position)
        await self.session.commit()
        await self.session.refresh(position)
        return position

    async def update_vehicle_status(
        self,
        vehicle: Vehicle,
        vehicle_status_id: UUID,
    ) -> VehicleStatus:
        """Met à jour le statut d'un véhicule."""
        status = await self.session.get(VehicleStatus, vehicle_status_id)
        if status is None:
            raise ValueError("Vehicle status not found")
        vehicle.status_id = vehicle_status_id
        await self.session.commit()
        await self.session.refresh(vehicle)
        return status
