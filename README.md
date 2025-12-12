# app-qg-api

API FastAPI sécurisée avec middleware Keycloak, connecteurs async pour PostgreSQL et RabbitMQ, logging JSON via structlog, et flux SSE `/events` pour les notifications temps réel.

## Structure du projet

```txt
src/app/
├── main.py              # Factory FastAPI + lifespan
├── core/
│   ├── config.py        # Settings Pydantic (prefixes APP_, POSTGRES_, RABBITMQ_, AUTH_, KEYCLOAK_)
│   └── logging.py       # Configuration structlog
├── api/
│   ├── dependencies.py  # Dépendances FastAPI
│   └── routes/          # Routes HTTP (/health, /events)
├── models/              # Modèles de données
└── services/
    ├── db/              # MongoDB (motor) + Postgres (SQLAlchemy async)
    └── messaging/       # RabbitMQ (aio-pika)
```

---

## Quickstart

### Prérequis

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (gestionnaire de packages)
- Docker (optionnel)

### Installation

```bash
uv sync
```

---

## 🚀 Lancement

### Sans Docker

#### Développement (hot reload)

```bash
uv run uvicorn app.main:app --reload --reload-dir src --app-dir src
```

> L'API est disponible sur <http://localhost:8000>

#### Production

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🔐 Auth Keycloak

- Les routes protégées utilisent une dépendance FastAPI avec HTTP Bearer (`Authorization: Bearer <jwt>`). Ajoutez `Depends(get_current_user)` sur les endpoints qui doivent être sécurisés (ex. `/events`). La route `/health` et la doc (`/docs`) restent publiques.
- Configuration minimale :

```env
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=my-realm
KEYCLOAK_CLIENT_ID=my-api
```

- Options utiles :
  - `AUTH_DISABLED=true` uniquement pour du développement local rapide.
- Les clés publiques sont chargées via JWKS (HTTP ou fichier `file:///...`) et mises en cache (`KEYCLOAK_CACHE_TTL_SECONDS`).

---

### Avec Docker

#### Build de l'image

```bash
docker build -t app-qg-api .
```

#### Développement (hot reload + services)

```bash
docker compose --profile dev up
```

> - API sur <http://localhost:8000> avec hot reload
> - MongoDB sur localhost:27017
> - PostgreSQL sur localhost:5432
> - RabbitMQ sur localhost:5672 (UI: <http://localhost:15672>)

#### Production

```bash
docker compose up -d
```

#### API seule (sans les bases de données)

```bash
docker run -p 8000:8000 app-qg-api
```

---

## 🧪 Tests

```bash
# Vérifier que l'API fonctionne (public)
curl http://localhost:8000/health

# Tester le flux SSE
curl -N -H "Authorization: Bearer <token>" http://localhost:8000/events

# Lancer les tests
uv run pytest
```

---

## ⚙️ Configuration

Variables d'environnement (fichier `.env` supporté, préfixes par domaine) :

| Variable | Description | Défaut |
|----------|-------------|--------|
| `APP_NAME` | Nom du service | `app-qg-api` |
| `APP_VERSION` | Version exposée | `latest` |
| `APP_ENVIRONMENT` | Environnement courant | `local` |
| `APP_DEBUG` | Mode debug | `false` |
| `APP_LOG_LEVEL` | Niveau de log | `INFO` |
| `APP_LOG_FORMAT` | Format des logs (`json` ou `console`) | `json` |
| `APP_CORS_ORIGINS` | Origines autorisées (CSV) | `*` |
| `APP_EVENTS_PING_INTERVAL_SECONDS` | Intervalle keepalive SSE | `25` |
| `POSTGRES_DSN` | URI PostgreSQL | `postgresql+asyncpg://postgres:postgres@localhost:5432/app` |
| `RABBITMQ_DSN` | URI RabbitMQ | `amqp://guest:guest@localhost:5672/` |
| `AUTH_DISABLED` | Désactiver l'auth (local/tests) | `false` |
| `KEYCLOAK_SERVER_URL` | URL de Keycloak | `http://localhost:8080` |
| `KEYCLOAK_REALM` | Nom du realm | `master` |
| `KEYCLOAK_CLIENT_ID` | Client ID | `app-qg-api` |
| `KEYCLOAK_AUDIENCE` | Audience attendue (optionnel) | `KEYCLOAK_CLIENT_ID` |
| `KEYCLOAK_CACHE_TTL_SECONDS` | Cache JWKS (s) | `300` |
| `KEYCLOAK_TIMEOUT_SECONDS` | Timeout HTTP pour Keycloak (s) | `3.0` |

---

## 📬 Messagerie

- Les queues utilisées sont déclarées dans `app/services/messaging/queues.py` (`SUB_QUEUES` pour la consommation, `PUB_QUEUES` pour la publication).
- L'API consomme toutes les queues listées dans `SUB_QUEUES` et route les messages selon le champ JSON `event`.
- Les événements connus sont listés dans `app/services/events/events.py`.
- Le corps attendu pour chaque message est un objet JSON du type `{"event": "<nom>", "payload": {...}}`. Les événements inconnus sont simplement journalisés.

---

## 📝 Logging

Logging JSON structuré via structlog :

```python
from app.core.logging import get_logger

logger = get_logger(__name__)
logger.bind(user_id=123).info("User logged in")
```

---

## CI/CD

GitHub Actions sur push/PR :

- `ruff check src tests`
- `pytest`
