"""
Tests pour l'endpoint /health.
"""

import pytest


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok(async_client, auth_headers):
    """Test que l'endpoint /health retourne un status 'ok'."""
    response = await async_client.get("/health", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_health_endpoint_response_structure(async_client, auth_headers):
    """Test la structure de la réponse de /health."""
    response = await async_client.get("/health", headers=auth_headers)
    data = response.json()

    assert "status" in data
    assert isinstance(data["status"], str)
