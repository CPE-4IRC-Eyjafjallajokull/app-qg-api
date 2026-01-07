"""
Routes métier pour le terrain.

Ce module expose les endpoints utilisés par les équipes terrain
pour accéder aux points d'intérêt et autres ressources nécessaires
sur le terrain.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_postgres_session
from app.api.routes.utils import fetch_one_or_404
from app.models import InterestPoint, InterestPointKind
from app.schemas.interest_points import InterestPointRead

router = APIRouter(prefix="/terrain", tags=["terrain"])


@router.post(
    "/interest-points/{kind_id}",
    response_model=list[InterestPointRead],
    summary="Liste les points d'intérêt par type",
    description="""
    Récupère tous les points d'intérêt correspondant à un type (kind) donné.
    
    Cette route est utilisée par les équipes terrain pour localiser
    les ressources disponibles selon leur catégorie (casernes, hôpitaux, etc.).
    """,
)
async def list_interest_points_by_kind(
    kind_id: UUID,
    session: AsyncSession = Depends(get_postgres_session),
) -> list[InterestPoint]:
    """
    Retourne la liste des points d'intérêt filtrés par leur type (kind_id).

    Args:
        kind_id: L'identifiant UUID du type de point d'intérêt.
        session: Session de base de données PostgreSQL.

    Returns:
        Liste des points d'intérêt correspondant au type demandé.

    Raises:
        HTTPException 404: Si le type de point d'intérêt n'existe pas.
    """
    # Vérifier que le type de point d'intérêt existe
    await fetch_one_or_404(
        session,
        select(InterestPointKind).where(
            InterestPointKind.interest_point_kind_id == kind_id
        ),
        "Interest point kind not found",
    )

    # Récupérer les points d'intérêt filtrés par kind_id
    result = await session.execute(
        select(InterestPoint)
        .options(selectinload(InterestPoint.kind))
        .where(InterestPoint.interest_point_kind_id == kind_id)
        .order_by(InterestPoint.name)
    )

    return result.scalars().all()
