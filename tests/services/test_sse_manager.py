import asyncio

import pytest

from app.services.events import SSEManager


@pytest.mark.asyncio
async def test_event_stream_sends_connected_and_counts_clients():
    manager = SSEManager(heartbeat_interval=0.05)

    stream = manager.event_stream()
    first_msg = await asyncio.wait_for(stream.__anext__(), timeout=0.1)

    assert "event: connected" in first_msg
    assert '"event": "connected"' in first_msg
    assert manager.client_count == 1

    await stream.aclose()
    assert manager.client_count == 0


@pytest.mark.asyncio
async def test_notify_delivers_to_stream_subscribers():
    manager = SSEManager(heartbeat_interval=0.05)

    stream = manager.event_stream()
    await stream.__anext__()  # connected

    await manager.notify("test_event", {"key": "value"})
    delivered = await asyncio.wait_for(stream.__anext__(), timeout=0.1)

    assert '"event": "test_event"' in delivered
    assert '"key": "value"' in delivered

    await stream.aclose()


@pytest.mark.asyncio
async def test_listen_filters_events():
    manager = SSEManager()

    listener = manager.listen(events=["keep"])
    pending = asyncio.create_task(listener.__anext__())
    await asyncio.sleep(0)

    await manager.notify("drop", {"foo": "bar"})
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(asyncio.shield(pending), timeout=0.05)

    await manager.notify("keep", {"ok": True})
    payload = await asyncio.wait_for(asyncio.shield(pending), timeout=0.1)

    assert payload["event"] == "keep"
    assert payload["data"]["ok"] is True

    await listener.aclose()


@pytest.mark.asyncio
async def test_disconnect_all_clears_clients():
    manager = SSEManager(heartbeat_interval=0.05)

    stream = manager.event_stream()
    await stream.__anext__()  # connected
    assert manager.client_count == 1

    await manager.disconnect_all()

    with pytest.raises(StopAsyncIteration):
        await stream.__anext__()

    assert manager.client_count == 0
