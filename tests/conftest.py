"""
Fixtures partagées pour tous les tests.
"""

import json
import os
import tempfile
import time
from pathlib import Path

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


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Generate a signed JWT for tests."""
    now = int(time.time())
    token = jwt.encode(
        {
            "sub": "test-user",
            "iss": TEST_ISSUER,
            "aud": TEST_CLIENT_ID,
            "iat": now,
            "exp": now + 3600,
            "preferred_username": "tester",
            "realm_access": {"roles": ["tester"]},
        },
        PRIVATE_KEY,
        algorithm="RS256",
        headers={"kid": TEST_KID},
    )
    return {"Authorization": f"Bearer {token}"}
