from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Coordinates(BaseModel):
    """Coordonnées géographiques (latitude, longitude)."""

    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(
        ..., ge=-90, le=90, description="Latitude en degrés décimaux"
    )
    longitude: float = Field(
        ..., ge=-180, le=180, description="Longitude en degrés décimaux"
    )


class RouteRequest(BaseModel):
    """Requête de calcul d'itinéraire."""

    model_config = ConfigDict(extra="forbid")

    from_coords: Coordinates = Field(..., alias="from", description="Point de départ")
    to: Coordinates = Field(..., description="Point d'arrivée")
    snap_start: bool = Field(
        default=False,
        description="Corriger le point de départ pour le placer sur la route la plus proche",
    )


class LineStringGeometry(BaseModel):
    """Géométrie GeoJSON de type LineString."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(default="LineString", description="Type de géométrie GeoJSON")
    coordinates: list[list[float]] = Field(
        ...,
        description="Liste de coordonnées [longitude, latitude]",
    )


class RouteResponse(BaseModel):
    """Réponse contenant l'itinéraire calculé."""

    model_config = ConfigDict(extra="forbid")

    distance_m: float = Field(..., description="Distance totale en mètres")
    duration_s: float = Field(..., description="Durée estimée en secondes")
    geometry: LineStringGeometry = Field(..., description="Tracé de l'itinéraire")
