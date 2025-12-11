import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.events import SSEManager


@pytest.fixture
def client_transport():
    return ASGITransport(app=app)


@pytest.mark.asyncio
async def test_health_endpoint_is_public(client_transport):
    async with AsyncClient(
        transport=client_transport, base_url="http://testserver"
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_sse_manager_event_stream_emits_connected_event():
    manager = SSEManager(heartbeat_interval=0.05)

    stream = manager.event_stream()
    first_message = await asyncio.wait_for(stream.__anext__(), timeout=0.1)

    assert "event: connected" in first_message
    assert '"event": "connected"' in first_message
    await stream.aclose()


@pytest.mark.asyncio
async def test_sse_manager_notify_dispatches_to_stream():
    manager = SSEManager(heartbeat_interval=0.05)

    stream = manager.event_stream()
    await stream.__anext__()  # connected

    await manager.notify("test", {"data": "hello"})
    delivered = await asyncio.wait_for(stream.__anext__(), timeout=0.1)

    assert '"event": "test"' in delivered
    assert '"hello"' in delivered
    await stream.aclose()
