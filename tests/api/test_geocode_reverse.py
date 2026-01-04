"""
Tests pour l'endpoint /geocode/reverse.
"""

import pytest

import app.api.routes.geocode as geocode_routes
from app.services.geocoding.nominatim import NominatimReverseGeocoder


@pytest.fixture
def geocoder_stub(monkeypatch):
    geocoder = NominatimReverseGeocoder()

    async def fake_fetch(lat: float, lon: float) -> dict:
        return {
            "address": {"road": "Rue Exemple", "city": "Paris"},
            "display_name": "Rue Exemple, Paris, France",
            "lat": lat,
            "lon": lon,
        }

    monkeypatch.setattr(geocoder, "_fetch", fake_fetch)
    monkeypatch.setattr(geocode_routes, "_geocoder", geocoder)
    return geocoder


@pytest.mark.asyncio
async def test_reverse_geocode_ok(async_client, auth_headers_viewer, geocoder_stub):
    headers = {**auth_headers_viewer, "X-Forwarded-For": "1.2.3.4"}
    response = await async_client.get(
        "/geocode/reverse?lat=48.8566&lon=2.3522", headers=headers
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["address"]["city"] == "Paris"
    assert payload["data"]["display_name"] == "Rue Exemple, Paris, France"


@pytest.mark.asyncio
async def test_reverse_geocode_missing_params(async_client, auth_headers_viewer):
    headers = {**auth_headers_viewer, "X-Forwarded-For": "1.2.3.4"}
    response = await async_client.get("/geocode/reverse?lat=48.0", headers=headers)

    assert response.status_code == 400
    payload = response.json()
    assert payload["ok"] is False
    assert "error" in payload


@pytest.mark.asyncio
async def test_reverse_geocode_throttle(
    async_client, auth_headers_viewer, geocoder_stub
):
    headers = {**auth_headers_viewer, "X-Forwarded-For": "1.2.3.4"}

    first = await async_client.get(
        "/geocode/reverse?lat=48.8566&lon=2.3522", headers=headers
    )
    second = await async_client.get(
        "/geocode/reverse?lat=48.8566&lon=2.3522", headers=headers
    )

    assert first.status_code == 200
    assert second.status_code == 429
