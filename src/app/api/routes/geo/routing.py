from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.schemas.routing import RouteRequest, RouteResponse
from app.services.routing import RoutingError, osrm_router

router = APIRouter(prefix="/route")
log = get_logger(__name__)


def _error_response(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"ok": False, "error": message},
    )


@router.post(
    "",
    response_model=RouteResponse,
    responses={
        200: {"description": "Itinéraire calculé avec succès"},
        400: {"description": "Paramètres invalides ou aucun itinéraire trouvé"},
        503: {"description": "Service de routage indisponible"},
    },
    summary="Calculer un itinéraire",
    description=(
        "Calcule un itinéraire entre un point de départ et un point d'arrivée. "
        "Retourne une polyline GeoJSON pour la simulation véhicule."
    ),
)
async def calculate_route(request: RouteRequest) -> RouteResponse | JSONResponse:
    """
    Calcule un itinéraire entre deux points.

    - **from**: Coordonnées du point de départ (latitude, longitude)
    - **to**: Coordonnées du point d'arrivée (latitude, longitude)
    - **snap_start**: Optionnel, corrige le point de départ sur la route la plus proche
    """
    log.info(
        "routing.route.request",
        from_lat=request.from_coords.latitude,
        from_lon=request.from_coords.longitude,
        to_lat=request.to.latitude,
        to_lon=request.to.longitude,
        snap_start=request.snap_start,
    )

    try:
        result = await osrm_router.route(
            from_lat=request.from_coords.latitude,
            from_lon=request.from_coords.longitude,
            to_lat=request.to.latitude,
            to_lon=request.to.longitude,
            snap_start=request.snap_start,
        )

        return RouteResponse(
            distance_m=result["distance_m"],
            duration_s=result["duration_s"],
            geometry=result["geometry"],
        )

    except RoutingError as exc:
        log.warning(
            "routing.route.error",
            error=exc.message,
            status_code=exc.status_code,
        )
        return _error_response(exc.message, exc.status_code)

    except Exception as exc:
        log.error("routing.route.unhandled_error", error=str(exc))
        return _error_response(
            "Internal server error",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
