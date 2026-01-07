"""
Tests pour les endpoints /terrain.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.main import app


@pytest.fixture
def mock_interest_point_kind():
    """Fixture pour créer un mock de InterestPointKind."""
    kind = MagicMock()
    kind.interest_point_kind_id = uuid.uuid4()
    kind.label = "Caserne"
    return kind


@pytest.fixture
def mock_interest_points(mock_interest_point_kind):
    """Fixture pour créer une liste de mocks de InterestPoint."""
    points = []
    for i in range(3):
        point = MagicMock()
        point.interest_point_id = uuid.uuid4()
        point.name = f"Point d'intérêt {i + 1}"
        point.address = f"{i + 1} rue de Test"
        point.zipcode = "75001"
        point.city = "Paris"
        point.latitude = 48.8566 + i * 0.01
        point.longitude = 2.3522 + i * 0.01
        point.interest_point_kind_id = mock_interest_point_kind.interest_point_kind_id
        point.kind = mock_interest_point_kind
        points.append(point)
    return points


@pytest.mark.asyncio
async def test_list_interest_points_by_kind_returns_points(
    async_client,
    auth_headers,
    mock_interest_point_kind,
    mock_interest_points,
):
    """Test que l'endpoint retourne les points d'intérêt pour un kind valide."""
    kind_id = mock_interest_point_kind.interest_point_kind_id

    # Mock de la session PostgreSQL
    mock_session = AsyncMock()

    # Premier appel: vérification que le kind existe
    mock_kind_result = MagicMock()
    mock_kind_result.scalar_one_or_none.return_value = mock_interest_point_kind

    # Deuxième appel: récupération des points d'intérêt
    mock_points_result = MagicMock()
    mock_points_result.scalars.return_value.all.return_value = mock_interest_points

    mock_session.execute = AsyncMock(
        side_effect=[mock_kind_result, mock_points_result]
    )

    # Injection du mock dans les dépendances
    async def override_get_postgres_session():
        yield mock_session

    from app.api.dependencies import get_postgres_session

    app.dependency_overrides[get_postgres_session] = override_get_postgres_session

    try:
        response = await async_client.get(
            f"/terrain/interest-points/{kind_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_interest_points_by_kind_not_found(
    async_client,
    auth_headers,
):
    """Test que l'endpoint retourne 404 si le kind n'existe pas."""
    unknown_kind_id = uuid.uuid4()

    # Mock de la session PostgreSQL
    mock_session = AsyncMock()

    # Le kind n'existe pas
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def override_get_postgres_session():
        yield mock_session

    from app.api.dependencies import get_postgres_session

    app.dependency_overrides[get_postgres_session] = override_get_postgres_session

    try:
        response = await async_client.get(
            f"/terrain/interest-points/{unknown_kind_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Interest point kind not found"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_interest_points_by_kind_empty_list(
    async_client,
    auth_headers,
    mock_interest_point_kind,
):
    """Test que l'endpoint retourne une liste vide si aucun point n'existe pour ce kind."""
    kind_id = mock_interest_point_kind.interest_point_kind_id

    # Mock de la session PostgreSQL
    mock_session = AsyncMock()

    # Le kind existe
    mock_kind_result = MagicMock()
    mock_kind_result.scalar_one_or_none.return_value = mock_interest_point_kind

    # Aucun point d'intérêt
    mock_points_result = MagicMock()
    mock_points_result.scalars.return_value.all.return_value = []

    mock_session.execute = AsyncMock(
        side_effect=[mock_kind_result, mock_points_result]
    )

    async def override_get_postgres_session():
        yield mock_session

    from app.api.dependencies import get_postgres_session

    app.dependency_overrides[get_postgres_session] = override_get_postgres_session

    try:
        response = await async_client.get(
            f"/terrain/interest-points/{kind_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_interest_points_by_kind_requires_auth(async_client):
    """Test que l'endpoint requiert une authentification."""
    kind_id = uuid.uuid4()

    response = await async_client.get(f"/terrain/interest-points/{kind_id}")

    assert response.status_code == 401
