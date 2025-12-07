import json

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_events_stream_yields_data():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        async with client.stream("GET", "/events") as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    payload = json.loads(line.removeprefix("data: ").strip())
                    assert payload["event"] == "connected"
                    break
