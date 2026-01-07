from fastapi import APIRouter

from app.api.routes.geo.geocode import router as geocode_router
from app.api.routes.geo.routing import router as routing_router

router = APIRouter(prefix="/geo", tags=["geo"])

# /geo/address - Géocodage (adresse ↔ coordonnées)
router.include_router(geocode_router)

# /geo/route - Calcul d'itinéraire
router.include_router(routing_router)
