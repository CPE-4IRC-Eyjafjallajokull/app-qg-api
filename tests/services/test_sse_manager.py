"""
Tests unitaires pour le SSEManager.
"""

import pytest

from app.services.events import SSEManager


class TestSSEManagerSubscribe:
    """Tests pour la méthode subscribe du SSEManager."""

    @pytest.mark.asyncio
    async def test_subscribe_yields_connected_event_immediately(self):
        """Test que le subscribe envoie un événement 'connected' immédiatement."""
        manager = SSEManager(heartbeat_interval=30)

        async for message in manager.subscribe():
            assert "event" in message
            assert "connected" in message
            assert "data:" in message
            break

    @pytest.mark.asyncio
    async def test_subscribe_increments_client_count(self):
        """Test que le subscribe incrémente le compteur de clients."""
        manager = SSEManager(heartbeat_interval=30)
        assert manager.client_count == 0

        gen = manager.subscribe()
        await gen.__anext__()  # Trigger subscription

        assert manager.client_count == 1


class TestSSEManagerBroadcast:
    """Tests pour la méthode broadcast du SSEManager."""

    @pytest.mark.asyncio
    async def test_broadcast_sends_message_to_subscribers(self):
        """Test que le broadcast envoie des messages à tous les clients."""
        manager = SSEManager(heartbeat_interval=30)

        gen = manager.subscribe()
        first_msg = await gen.__anext__()  # connected event

        await manager.broadcast("test_event", {"key": "value"})
        second_msg = await gen.__anext__()

        assert "connected" in first_msg
        assert "test_event" in second_msg
        assert "value" in second_msg

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_clients(self):
        """Test que le broadcast envoie à plusieurs clients."""
        manager = SSEManager(heartbeat_interval=30)

        gen1 = manager.subscribe()
        gen2 = manager.subscribe()

        await gen1.__anext__()  # connected
        await gen2.__anext__()  # connected

        assert manager.client_count == 2

        await manager.broadcast("multi", {"data": "test"})

        msg1 = await gen1.__anext__()
        msg2 = await gen2.__anext__()

        assert "multi" in msg1
        assert "multi" in msg2


class TestSSEManagerDisconnect:
    """Tests pour la déconnexion des clients SSE."""

    @pytest.mark.asyncio
    async def test_disconnect_all_clears_clients(self):
        """Test que disconnect_all déconnecte tous les clients."""
        manager = SSEManager(heartbeat_interval=30)

        gen = manager.subscribe()
        await gen.__anext__()

        assert manager.client_count == 1

        await manager.disconnect_all()

        # Le client reçoit None et se déconnecte
        assert manager.client_count == 0
