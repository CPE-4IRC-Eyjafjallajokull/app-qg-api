"""
Fixtures partagées pour tous les tests.
"""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient

TEST_ISSUER = "http://keycloak.test/realms/test"
TEST_CLIENT_ID = "test-api"
TEST_KID = "test-key"


def _bootstrap_keycloak_test_env() -> tuple[rsa.RSAPrivateKey, Path]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    jwk_dict = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(public_key))
    jwk_dict.update({"kid": TEST_KID, "use": "sig", "alg": "RS256"})

    tmp_dir = Path(tempfile.mkdtemp())
    jwks_path = tmp_dir / "jwks.json"
    jwks_path.write_text(json.dumps({"keys": [jwk_dict]}))

    os.environ["KEYCLOAK_JWKS_URL"] = jwks_path.as_uri()
    os.environ["KEYCLOAK_ISSUER"] = TEST_ISSUER
    os.environ["KEYCLOAK_CLIENT_ID"] = TEST_CLIENT_ID
    os.environ["KEYCLOAK_AUDIENCE"] = TEST_CLIENT_ID

    return private_key, jwks_path


PRIVATE_KEY, JWKS_PATH = _bootstrap_keycloak_test_env()

from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def mock_external_services():
    """Mock automatiquement tous les services externes pour éviter les connexions réelles."""
    # Mock PostgreSQL
    mock_postgres = MagicMock()
    mock_postgres.connect = AsyncMock()
    mock_postgres.close = AsyncMock()
    mock_postgres.get_session = AsyncMock()

    # Mock RabbitMQ
    mock_rabbitmq = MagicMock()
    mock_rabbitmq.connect = AsyncMock()
    mock_rabbitmq.close = AsyncMock()
    mock_rabbitmq.get_connection = AsyncMock()

    # Mock Subscriptions
    mock_subscriptions = MagicMock()
    mock_subscriptions.start = AsyncMock()
    mock_subscriptions.stop = AsyncMock()

    # Inject les mocks dans l'app state
    app.state.postgres = mock_postgres
    app.state.rabbitmq = mock_rabbitmq
    app.state.subscriptions = mock_subscriptions

    yield

    # Cleanup (optionnel)
    if hasattr(app.state, "postgres"):
        delattr(app.state, "postgres")
    if hasattr(app.state, "rabbitmq"):
        delattr(app.state, "rabbitmq")
    if hasattr(app.state, "subscriptions"):
        delattr(app.state, "subscriptions")


@pytest.fixture
def client_transport():
    """Transport ASGI pour les tests HTTP."""
    return ASGITransport(app=app)


@pytest.fixture
async def async_client(client_transport):
    """Client HTTP asynchrone pour les tests d'API."""
    async with AsyncClient(
        transport=client_transport, base_url="http://testserver"
    ) as client:
        yield client


def _build_auth_headers(roles: list[str]) -> dict[str, str]:
    now = int(time.time())
    token = jwt.encode(
        {
            "sub": "test-user",
            "iss": TEST_ISSUER,
            "aud": TEST_CLIENT_ID,
            "iat": now,
            "exp": now + 3600,
            "preferred_username": "tester",
            "realm_access": {"roles": roles},
        },
        PRIVATE_KEY,
        algorithm="RS256",
        headers={"kid": TEST_KID},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Generate a signed JWT for tests."""
    return _build_auth_headers(["tester"])


@pytest.fixture
def auth_headers_viewer() -> dict[str, str]:
    """JWT with read-only role for protected GET endpoints."""
    return _build_auth_headers(["qg-viewer"])
