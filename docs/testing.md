# Guide de Tests

## Architecture de Tests

Les tests de l'application sont configurés pour **ne pas nécessiter de services externes** (PostgreSQL, RabbitMQ, Keycloak réel). Cela permet d'exécuter les tests dans la CI GitHub Actions sans infrastructure supplémentaire.

## Services Mockés

### 1. Keycloak (Authentification)
- **Configuration** : Un serveur Keycloak mocké est configuré dans `tests/conftest.py`
- **Clés JWKS** : Générées en mémoire et stockées dans un fichier temporaire
- **Tokens JWT** : Signés avec une clé privée de test
- **Variables d'environnement** :
  ```python
  KEYCLOAK_JWKS_URL=file:///tmp/xxxxx/jwks.json
  KEYCLOAK_ISSUER=http://keycloak.test/realms/test
  KEYCLOAK_CLIENT_ID=test-api
  KEYCLOAK_AUDIENCE=test-api
  ```

### 2. PostgreSQL
- **Mock** : Fixture `autouse` dans `conftest.py`
- **Méthodes mockées** :
  - `connect()` : AsyncMock
  - `close()` : AsyncMock
  - `get_session()` : AsyncMock

### 3. RabbitMQ
- **Mock** : Fixture `autouse` dans `conftest.py`
- **Méthodes mockées** :
  - `connect()` : AsyncMock
  - `close()` : AsyncMock
  - `get_connection()` : AsyncMock

### 4. Subscriptions (ApplicationSubscriptions)
- **Mock** : Fixture `autouse` dans `conftest.py`
- **Méthodes mockées** :
  - `start()` : AsyncMock
  - `stop()` : AsyncMock

## Fixtures Disponibles

### `async_client`
Client HTTP asynchrone pour tester les endpoints de l'API.

```python
@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
```

### `auth_headers`
En-têtes d'authentification avec un JWT valide et le rôle `tester`.

```python
@pytest.mark.asyncio
async def test_protected_endpoint(async_client, auth_headers):
    response = await async_client.get("/protected", headers=auth_headers)
    assert response.status_code == 200
```

### `auth_headers_viewer`
En-têtes d'authentification avec un JWT valide et le rôle `qg-viewer`.

```python
@pytest.mark.asyncio
async def test_viewer_endpoint(async_client, auth_headers_viewer):
    response = await async_client.get("/read-only", headers=auth_headers_viewer)
    assert response.status_code == 200
```

## Exécution des Tests

### En local
```bash
# Tous les tests
uv run pytest

# Avec verbosité
uv run pytest -v

# Avec couverture
uv run pytest --cov=src --cov-report=term-missing
```

### Dans la CI
Les tests s'exécutent automatiquement via GitHub Actions sur :
- Chaque push sur `main`
- Chaque pull request vers `main`

Le workflow CI est défini dans `.github/workflows/ci.yml`.

## Bonnes Pratiques

1. **Ne jamais se connecter à de vrais services** dans les tests
2. **Utiliser les fixtures** fournies dans `conftest.py`
3. **Mocker les services externes** spécifiques aux tests si nécessaire
4. **Tester les comportements**, pas les implémentations
5. **Marquer les tests async** avec `@pytest.mark.asyncio`

## Exemple de Test avec Mock Spécifique

Si vous avez besoin de mocker un service spécifique pour un test :

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_geocode_endpoint(async_client, auth_headers_viewer, monkeypatch):
    # Mock du geocoder
    from app.api.routes import geocode as geocode_routes
    from app.services.geocoding.nominatim import NominatimReverseGeocoder
    
    geocoder = NominatimReverseGeocoder()
    
    async def fake_fetch(lat: float, lon: float) -> dict:
        return {
            "address": {"city": "Paris"},
            "display_name": "Paris, France",
            "lat": lat,
            "lon": lon,
        }
    
    monkeypatch.setattr(geocoder, "_fetch", fake_fetch)
    monkeypatch.setattr(geocode_routes, "_geocoder", geocoder)
    
    response = await async_client.get(
        "/geocode/reverse?lat=48.8566&lon=2.3522",
        headers={**auth_headers_viewer, "X-Forwarded-For": "1.2.3.4"}
    )
    
    assert response.status_code == 200
```

## Couverture de Code

La couverture de code est générée lors de l'exécution des tests et uploadée sur Codecov dans la CI.

Pour voir la couverture localement :
```bash
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html
```
