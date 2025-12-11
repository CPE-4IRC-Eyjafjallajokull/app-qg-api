from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
import jwt
from fastapi import HTTPException, status
from jwt import InvalidTokenError
from jwt.algorithms import Algorithm, get_default_algorithms

from app.core.logging import get_logger

if TYPE_CHECKING:
    from app.core.config import Settings

log = get_logger(__name__)


@dataclass(slots=True)
class KeycloakConfig:
    issuer: str
    jwks_url: str
    client_id: str
    audience: str
    cache_ttl_seconds: int = 300
    timeout_seconds: float = 3.0

    @classmethod
    def from_settings(cls, settings: "Settings") -> "KeycloakConfig":
        kc = settings.keycloak

        issuer = kc.issuer
        jwks_url = kc.jwks_url
        client_id = kc.client_id
        # Default audience to client_id when not explicitly provided to keep validation permissive for single-audience clients.
        audience = kc.audience or kc.client_id

        return cls(
            issuer=issuer,
            jwks_url=jwks_url,
            client_id=client_id,
            audience=audience,
            cache_ttl_seconds=kc.cache_ttl_seconds,
            timeout_seconds=kc.timeout_seconds,
        )


@dataclass(slots=True)
class AuthenticatedUser:
    subject: str
    username: str | None
    email: str | None
    roles: list[str]
    claims: dict[str, Any]


class KeycloakAuthenticator:
    """Validate Keycloak JWTs and expose a normalized user."""

    def __init__(
        self,
        config: KeycloakConfig,
        http_client: httpx.AsyncClient | None = None,
    ):
        self._config = config
        self._jwks: list[dict[str, Any]] | None = None
        self._jwks_expiry: datetime | None = None
        self._http_client = http_client or httpx.AsyncClient(follow_redirects=True)
        self._owns_http_client = http_client is None

    @property
    def config(self) -> KeycloakConfig:
        return self._config

    async def aclose(self) -> None:
        """Close the underlying HTTP client if owned."""
        if self._owns_http_client:
            await self._http_client.aclose()

    async def authenticate(self, token: str) -> AuthenticatedUser:
        """Validate a bearer token and return the authenticated user."""
        header = self._get_unverified_header(token)
        alg = header.get("alg")
        kid = header.get("kid")

        if not alg or not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token header",
                headers={"WWW-Authenticate": "Bearer"},
            )

        keys = await self._load_jwks()
        public_key = self._select_public_key(keys, kid, alg)

        try:
            claims = jwt.decode(
                token,
                key=public_key,
                algorithms=[alg],
                audience=self._config.audience,
                issuer=self._config.issuer,
                options={"require": ["exp", "iat", "iss", "aud"]},
            )
        except InvalidTokenError as exc:
            log.warning("auth.token_invalid", reason=str(exc))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        user = AuthenticatedUser(
            subject=claims.get("sub", ""),
            username=claims.get("preferred_username")
            or claims.get("email")
            or claims.get("sub"),
            email=claims.get("email"),
            roles=self._extract_roles(claims),
            claims=claims,
        )
        log.debug("auth.user_authenticated", sub=user.subject, roles=user.roles)
        return user

    async def _load_jwks(self) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        if self._jwks and self._jwks_expiry and now < self._jwks_expiry:
            return self._jwks

        keys = await self._fetch_jwks()
        self._jwks = keys
        self._jwks_expiry = now + timedelta(seconds=self._config.cache_ttl_seconds)
        log.info(
            "auth.jwks.loaded",
            jwks_url=self._config.jwks_url,
            expires_at=self._jwks_expiry.isoformat(),
        )
        return keys

    async def _fetch_jwks(self) -> list[dict[str, Any]]:
        url = self._config.jwks_url
        if url.startswith("file://"):
            path = Path(url.removeprefix("file://"))
            return self._read_jwks_from_path(path)
        if url.startswith("/"):
            return self._read_jwks_from_path(Path(url))

        try:
            response = await self._http_client.get(
                url, timeout=self._config.timeout_seconds
            )
            response.raise_for_status()
            payload = response.json()
            keys = payload.get("keys")
        except Exception as exc:  # noqa: BLE001
            log.error("auth.jwks.fetch_failed", error=str(exc), url=url)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch Keycloak signing keys",
            ) from exc

        if not keys:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Keycloak JWKS is empty",
            )
        return keys

    def _read_jwks_from_path(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Keycloak JWKS file not found",
            )
        payload = json.loads(path.read_text())
        keys = payload.get("keys")
        if not keys:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Keycloak JWKS file is empty",
            )
        return keys

    def _select_public_key(self, keys: list[dict[str, Any]], kid: str, alg: str) -> Any:
        key_data = next((key for key in keys if key.get("kid") == kid), None)
        if not key_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Signing key not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        algorithm: Algorithm | None = get_default_algorithms().get(alg)
        if not algorithm:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unsupported signing algorithm",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            # Convert the JWK to a public key usable by PyJWT
            return algorithm.from_jwk(json.dumps(key_data))
        except Exception as exc:  # noqa: BLE001
            log.error("auth.public_key.parse_failed", error=str(exc), kid=kid)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signing key",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

    @staticmethod
    def _extract_roles(claims: dict[str, Any]) -> list[str]:
        roles = set(claims.get("realm_access", {}).get("roles", []) or [])

        resource_access = claims.get("resource_access", {})
        for client_roles in resource_access.values():
            roles.update(client_roles.get("roles", []) or [])

        return sorted(roles)

    @staticmethod
    def _get_unverified_header(token: str) -> dict[str, Any]:
        try:
            return jwt.get_unverified_header(token)
        except InvalidTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
