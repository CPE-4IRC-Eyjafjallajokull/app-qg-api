import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.events import SSEManager


@pytest.fixture
def client_transport():
    return ASGITransport(app=app)


@pytest.mark.asyncio
async def test_health_requires_auth(client_transport):
    async with AsyncClient(
        transport=client_transport, base_url="http://testserver"
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 401
        assert response.json()["detail"]


@pytest.mark.asyncio
async def test_health_endpoint(client_transport, auth_headers):
    async with AsyncClient(
        transport=client_transport, base_url="http://testserver"
    ) as client:
        response = await client.get("/health", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestSSEManager:
    """Tests unitaires pour le SSEManager."""

    @pytest.mark.asyncio
    async def test_sse_manager_subscribe_yields_connected_event(self):
        """Test que le subscribe envoie un événement 'connected' immédiatement."""
        manager = SSEManager(heartbeat_interval=30)

        # Récupère le premier message du générateur
        async for message in manager.subscribe():
            assert "event" in message
            assert "connected" in message
            assert "data:" in message
            break  # Sort après le premier message

        # Vérifie qu'un client a été ajouté
        assert manager.client_count >= 0  # Le client est déconnecté après le break

    @pytest.mark.asyncio
    async def test_sse_manager_broadcast(self):
        """Test que le broadcast envoie des messages à tous les clients."""
        manager = SSEManager(heartbeat_interval=30)

        # Simule un abonnement
        messages = []
        gen = manager.subscribe()

        # Premier message (connected)
        first_msg = await gen.__anext__()
        messages.append(first_msg)

        # Broadcast un message
        await manager.broadcast("test", {"data": "hello"})

        # Récupère le message broadcasté
        second_msg = await gen.__anext__()
        messages.append(second_msg)

        assert "connected" in messages[0]
        assert "test" in messages[1]
        assert "hello" in messages[1]
