# app-qg-api

API FastAPI avec connecteurs async pour MongoDB, PostgreSQL et RabbitMQ, logging JSON via structlog, et flux SSE `/events` pour les notifications temps réel.

## Structure du projet

```txt
src/app/
├── main.py              # Factory FastAPI + lifespan
├── core/
│   ├── config.py        # Settings Pydantic (prefix APP_)
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
# Vérifier que l'API fonctionne
curl http://localhost:8000/health

# Tester le flux SSE
curl -N http://localhost:8000/events

# Lancer les tests
uv run pytest
```

---

## ⚙️ Configuration

Variables d'environnement (fichier `.env` supporté, prefix `APP_`) :

| Variable | Description | Défaut |
|----------|-------------|--------|
| `APP_APP_NAME` | Nom du service | `app-qg-api` |
| `APP_DEBUG` | Mode debug | `false` |
| `APP_LOG_LEVEL` | Niveau de log | `INFO` |
| `APP_MONGO_DSN` | URI MongoDB | `mongodb://localhost:27017/app` |
| `APP_POSTGRES_DSN` | URI PostgreSQL | `postgresql+asyncpg://...` |
| `APP_RABBITMQ_DSN` | URI RabbitMQ | `amqp://guest:guest@localhost:5672/` |
| `APP_EVENTS_PING_INTERVAL_SECONDS` | Intervalle keepalive SSE | `15` |

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
