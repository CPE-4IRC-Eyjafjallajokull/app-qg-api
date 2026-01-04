from __future__ import annotations

import math
import time
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


class GeocodeError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class TTLCache:
    def __init__(self, ttl_seconds: float) -> None:
        self._ttl_seconds = ttl_seconds
        self._data: dict[str, tuple[float, dict[str, Any]]] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        now = time.monotonic()
        entry = self._data.get(key)
        if not entry:
            return None
        expires_at, value = entry
        if expires_at <= now:
            self._data.pop(key, None)
            return None
        return value

    def set(self, key: str, value: dict[str, Any]) -> None:
        self._data[key] = (time.monotonic() + self._ttl_seconds, value)


class IPThrottle:
    def __init__(self, min_interval_seconds: float) -> None:
        self._min_interval_seconds = min_interval_seconds
        self._last_request: dict[str, float] = {}

    def check(self, client_ip: str) -> float | None:
        now = time.monotonic()
        last = self._last_request.get(client_ip)
        if last is not None:
            elapsed = now - last
            if elapsed < self._min_interval_seconds:
                return self._min_interval_seconds - elapsed
        self._last_request[client_ip] = now
        return None


class NominatimReverseGeocoder:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        user_agent: str | None = None,
        accept_language: str | None = None,
        timeout_seconds: float | None = None,
        cache_ttl_seconds: float | None = None,
        throttle_seconds: float | None = None,
        cache_rounding_precision: int | None = None,
    ) -> None:
        config = settings.nominatim
        self._base_url = (base_url or config.base_url).rstrip("/")
        self._timeout_seconds = timeout_seconds or config.timeout_seconds
        self._accept_language = accept_language or config.accept_language
        self._user_agent = (
            user_agent
            or config.user_agent
            or f"{settings.app.name}/{settings.app.version} (reverse-geocoding)"
        )
        self._cache_rounding_precision = (
            cache_rounding_precision
            if cache_rounding_precision is not None
            else config.cache_rounding_precision
        )
        self._cache = TTLCache(
            cache_ttl_seconds
            if cache_ttl_seconds is not None
            else config.cache_ttl_seconds
        )
        self._throttle = IPThrottle(
            throttle_seconds
            if throttle_seconds is not None
            else config.throttle_seconds
        )

    def check_throttle(self, client_ip: str) -> float | None:
        return self._throttle.check(client_ip)

    async def reverse(self, lat: float, lon: float) -> dict[str, Any]:
        cache_key = self._cache_key(lat, lon)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        payload = await self._fetch(lat, lon)
        self._cache.set(cache_key, payload)
        return payload

    def _cache_key(self, lat: float, lon: float) -> str:
        precision = self._cache_rounding_precision
        return f"{lat:.{precision}f},{lon:.{precision}f}"

    async def _fetch(self, lat: float, lon: float) -> dict[str, Any]:
        params = {
            "format": "jsonv2",
            "lat": lat,
            "lon": lon,
            "addressdetails": 1,
        }
        headers = {
            "User-Agent": self._user_agent,
            "Accept-Language": self._accept_language,
        }

        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout_seconds,
                headers=headers,
                follow_redirects=True,
            ) as client:
                response = await client.get("/reverse", params=params)
        except httpx.TimeoutException as exc:
            log.warning("geocode.timeout", error=str(exc))
            raise GeocodeError("Reverse geocoding timed out", status_code=504) from exc
        except httpx.HTTPError as exc:
            log.warning("geocode.http_error", error=str(exc))
            raise GeocodeError("Upstream connection error", status_code=502) from exc

        if response.status_code != 200:
            log.warning("geocode.upstream_status", status=response.status_code)
            raise GeocodeError(
                f"Nominatim error ({response.status_code})", status_code=502
            )

        try:
            payload = response.json()
        except ValueError as exc:
            log.warning("geocode.invalid_json", error=str(exc))
            raise GeocodeError("Invalid JSON from Nominatim", status_code=502) from exc

        if not isinstance(payload, dict):
            raise GeocodeError("Unexpected response from Nominatim", status_code=502)

        if payload.get("error"):
            raise GeocodeError(
                f"Nominatim error: {payload.get('error')}", status_code=502
            )

        address = payload.get("address")
        if not isinstance(address, dict):
            address = {}

        display_name = payload.get("display_name")
        if not display_name:
            raise GeocodeError("Unexpected response from Nominatim", status_code=502)

        return {
            "address": address,
            "display_name": display_name,
            "lat": self._coerce_coordinate(payload.get("lat"), lat),
            "lon": self._coerce_coordinate(payload.get("lon"), lon),
        }

    @staticmethod
    def _coerce_coordinate(value: Any, fallback: float) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return fallback
        if not math.isfinite(number):
            return fallback
        return number


reverse_geocoder = NominatimReverseGeocoder()
