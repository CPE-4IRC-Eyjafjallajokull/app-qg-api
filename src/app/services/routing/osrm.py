from __future__ import annotations

import ipaddress
import math
from typing import Any
from urllib.parse import quote, urlparse

import httpx
import polyline

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


class RoutingError(Exception):
    """Erreur lors du calcul d'itinéraire."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class OSRMRouter:
    """Client pour le service OSRM (Open Source Routing Machine)."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        config = settings.osrm
        self._base_url = (base_url or config.base_url).rstrip("/")
        self._validate_base_url(self._base_url)
        self._username = username or config.username
        self._password = password or config.password
        self._timeout_seconds = timeout_seconds or config.timeout_seconds

    def _get_auth(self) -> httpx.BasicAuth | None:
        """Retourne l'authentification BasicAuth si configurée."""
        if self._username and self._password:
            return httpx.BasicAuth(self._username, self._password)
        return None

    @staticmethod
    def _validate_base_url(base_url: str) -> None:
        """Valide l'URL de base pour eviter les redirections internes."""
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("OSRM base_url must use http or https")
        if not parsed.hostname:
            raise ValueError("OSRM base_url must include a hostname")
        if parsed.username or parsed.password:
            raise ValueError("OSRM base_url must not contain credentials")
        if parsed.query or parsed.fragment:
            raise ValueError("OSRM base_url must not include query or fragment")

        try:
            ip_addr = ipaddress.ip_address(parsed.hostname)
        except ValueError:
            return

        if ip_addr.is_private or ip_addr.is_loopback or ip_addr.is_link_local:
            raise ValueError("OSRM base_url must not target private or loopback IPs")

    @staticmethod
    def _format_coord(value: float, *, min_value: float, max_value: float) -> str:
        if not math.isfinite(value):
            raise RoutingError("Invalid coordinate value", status_code=400)
        if value < min_value or value > max_value:
            raise RoutingError("Coordinate out of range", status_code=400)
        return f"{value:.6f}"

    def _build_route_path(
        self,
        *,
        from_lat: float,
        from_lon: float,
        to_lat: float,
        to_lon: float,
    ) -> str:
        from_lat_str = self._format_coord(from_lat, min_value=-90.0, max_value=90.0)
        from_lon_str = self._format_coord(from_lon, min_value=-180.0, max_value=180.0)
        to_lat_str = self._format_coord(to_lat, min_value=-90.0, max_value=90.0)
        to_lon_str = self._format_coord(to_lon, min_value=-180.0, max_value=180.0)
        coordinates = f"{from_lon_str},{from_lat_str};{to_lon_str},{to_lat_str}"
        safe_coordinates = quote(coordinates, safe=";,.-0123456789")
        return f"/route/v1/driving/{safe_coordinates}"

    async def route(
        self,
        from_lat: float,
        from_lon: float,
        to_lat: float,
        to_lon: float,
        *,
        snap_start: bool = False,
    ) -> dict[str, Any]:
        """
        Calcule un itinéraire entre deux points.

        Args:
            from_lat: Latitude du point de départ
            from_lon: Longitude du point de départ
            to_lat: Latitude du point d'arrivée
            to_lon: Longitude du point d'arrivée
            snap_start: Si True, corrige le point de départ sur la route la plus proche

        Returns:
            Dictionnaire contenant distance_m, duration_s et geometry

        Raises:
            RoutingError: En cas d'erreur de calcul d'itinéraire
        """
        # Format OSRM: /route/v1/{profile}/{coordinates}
        # Les coordonnées sont au format lon,lat;lon,lat
        route_path = self._build_route_path(
            from_lat=from_lat,
            from_lon=from_lon,
            to_lat=to_lat,
            to_lon=to_lon,
        )

        # Paramètres OSRM
        params: dict[str, Any] = {
            "overview": "full",  # Géométrie complète
            "geometries": "polyline",  # Format polyline encodé
            "steps": "false",  # Pas besoin des étapes détaillées
        }

        # Si snap_start est activé, on demande un snapping plus strict
        if snap_start:
            params["snapping"] = "any"

        log.debug(
            "osrm.route.request",
            url=f"{self._base_url}{route_path}",
            from_coords=(from_lat, from_lon),
            to_coords=(to_lat, to_lon),
            snap_start=snap_start,
        )

        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout_seconds,
            ) as client:
                response = await client.get(
                    route_path,
                    params=params,
                    auth=self._get_auth(),
                )

                if response.status_code == 401:
                    log.error("osrm.route.auth_error", status_code=response.status_code)
                    raise RoutingError(
                        "Authentication failed with routing service", status_code=503
                    )

                if response.status_code != 200:
                    log.error(
                        "osrm.route.http_error",
                        status_code=response.status_code,
                        response_text=response.text[:500],
                    )
                    raise RoutingError(
                        f"Routing service returned HTTP {response.status_code}",
                        status_code=503,
                    )

                data = response.json()

        except httpx.TimeoutException:
            log.error("osrm.route.timeout", timeout=self._timeout_seconds)
            raise RoutingError("Routing service timeout", status_code=503)
        except httpx.RequestError as exc:
            log.error("osrm.route.request_error", error=str(exc))
            raise RoutingError("Routing service unavailable", status_code=503)

        # Vérification de la réponse OSRM
        if data.get("code") != "Ok":
            error_code = data.get("code", "Unknown")
            error_message = data.get("message", "No route found")
            log.warning(
                "osrm.route.no_route",
                code=error_code,
                message=error_message,
            )
            raise RoutingError(f"No route found: {error_message}", status_code=400)

        routes = data.get("routes", [])
        if not routes:
            raise RoutingError("No route found", status_code=400)

        route = routes[0]

        # Décoder la polyline encodée en coordonnées
        encoded_geometry = route.get("geometry", "")
        decoded_coords = polyline.decode(encoded_geometry)

        # Convertir en format GeoJSON [lon, lat]
        geojson_coords = [[lon, lat] for lat, lon in decoded_coords]

        result = {
            "distance_m": route.get("distance", 0),
            "duration_s": route.get("duration", 0),
            "geometry": {
                "type": "LineString",
                "coordinates": geojson_coords,
            },
        }

        log.debug(
            "osrm.route.success",
            distance_m=result["distance_m"],
            duration_s=result["duration_s"],
            points_count=len(geojson_coords),
        )

        return result


# Instance globale du router
osrm_router = OSRMRouter()
