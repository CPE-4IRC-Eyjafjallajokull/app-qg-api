from __future__ import annotations

import math

from fastapi import APIRouter, Query, Request, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.services.geocoding.nominatim import GeocodeError, reverse_geocoder

router = APIRouter(prefix="/address", tags=["address"])
log = get_logger(__name__)
_geocoder = reverse_geocoder


def _error_response(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"ok": False, "error": message},
    )


def _get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return "unknown"


def _parse_coordinate(value: str, name: str) -> tuple[float | None, str | None]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None, f"{name} must be a valid float"
    if not math.isfinite(number):
        return None, f"{name} must be a finite float"
    return number, None


@router.get("/reverse")
async def reverse_geocode(
    request: Request,
    lat: str | None = Query(
        default=None, description="Latitude in decimal degrees", alias="lat"
    ),
    lon: str | None = Query(
        default=None, description="Longitude in decimal degrees", alias="lon"
    ),
):
    if lat is None:
        return _error_response("Missing lat parameter", status.HTTP_400_BAD_REQUEST)

    if lon is None:
        return _error_response("Missing lon parameter", status.HTTP_400_BAD_REQUEST)

    lat_value, lat_error = _parse_coordinate(lat, "lat")
    if lat_error:
        return _error_response(lat_error, status.HTTP_400_BAD_REQUEST)

    lon_value, lon_error = _parse_coordinate(lon, "lon")
    if lon_error:
        return _error_response(lon_error, status.HTTP_400_BAD_REQUEST)

    if not (-90 <= lat_value <= 90):
        return _error_response(
            "lat must be between -90 and 90", status.HTTP_400_BAD_REQUEST
        )
    if not (-180 <= lon_value <= 180):
        return _error_response(
            "lon must be between -180 and 180",
            status.HTTP_400_BAD_REQUEST,
        )

    client_ip = _get_client_ip(request)
    retry_after = _geocoder.check_throttle(client_ip)
    if retry_after is not None:
        retry_after_header = str(max(1, int(math.ceil(retry_after))))
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"ok": False, "error": "Too many requests"},
            headers={"Retry-After": retry_after_header},
        )

    try:
        payload = await _geocoder.reverse(lat_value, lon_value)
    except GeocodeError as exc:
        return _error_response(exc.message, exc.status_code)
    except Exception as exc:
        log.error("geocode.unhandled_error", error=str(exc))
        return _error_response(
            "Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return {"ok": True, "data": payload}
