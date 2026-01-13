from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import VehicleAssignmentRequest

ASSIGNMENT_REQUEST_IN_PROGRESS_DETAIL = "Assignment request already in progress."


async def acquire_assignment_request_lock(
    session: AsyncSession,
    incident_id: UUID,
    requested_by_operator_id: UUID | None = None,
) -> bool:
    stmt = (
        pg_insert(VehicleAssignmentRequest)
        .values(
            incident_id=incident_id,
            requested_by_operator_id=requested_by_operator_id,
        )
        .on_conflict_do_nothing(index_elements=[VehicleAssignmentRequest.incident_id])
        .returning(VehicleAssignmentRequest.incident_id)
    )

    try:
        result = await session.execute(stmt)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise

    return result.scalar_one_or_none() is not None


async def release_assignment_request_lock(
    session: AsyncSession, incident_id: UUID
) -> None:
    try:
        await session.execute(
            delete(VehicleAssignmentRequest).where(
                VehicleAssignmentRequest.incident_id == incident_id
            )
        )
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise


async def release_assignment_request_lock_safely(
    session: AsyncSession, incident_id: UUID
) -> None:
    try:
        await release_assignment_request_lock(session, incident_id)
    except SQLAlchemyError:
        return
