"""
Fixtures partagées pour tous les tests.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client_transport():
    """Transport ASGI pour les tests HTTP."""
    return ASGITransport(app=app)


@pytest.fixture
async def async_client(client_transport):
    """Client HTTP asynchrone pour les tests d'API."""
    async with AsyncClient(
        transport=client_transport, base_url="http://testserver"
    ) as client:
        yield client
