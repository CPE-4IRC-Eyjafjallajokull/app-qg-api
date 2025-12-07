## Overview

Starter FastAPI service with async-ready connectors for MongoDB, PostgreSQL, and RabbitMQ, JSON logging via structlog, and an HTTP SSE `/events` stream for real-time pushes.

## Project layout

- `src/app/main.py` — FastAPI app factory with lifespan-managed connectors.
- `src/app/core/config.py` — Pydantic settings (env prefix `APP_`).
- `src/app/core/logging.py` — stdlib + structlog JSON logger setup.
- `src/app/api/routes` — HTTP routes (`/health`, `/events` SSE).
- `src/app/services/db` — MongoDB (motor) and Postgres (SQLAlchemy async) helpers.
- `src/app/services/messaging` — RabbitMQ (aio-pika) helper.
- `tests/` — smoke tests for health and `/events`.
- `.github/workflows/ci.yml` — lint + test on push/PR.

## Quickstart

Prereqs: Python 3.12+, MongoDB/PostgreSQL/RabbitMQ if you want to connect to them.

1) Install dependencies (dev extras include lint/test tools):
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

2) Run the API:
```bash
uvicorn app.main:app --reload --app-dir src
```

3) Try it:
- Health check: `curl http://localhost:8000/health`
- HTTP stream (SSE-style): `curl -N http://localhost:8000/events`

## Configuration

Environment variables (loaded from `.env` if present, prefixed with `APP_`):
- `APP_APP_NAME` — service name (`app-qg-api`).
- `APP_DEBUG` — toggle debug mode (`false`).
- `APP_LOG_LEVEL` — e.g. `INFO`, `DEBUG`.
- `APP_MONGO_DSN` — `mongodb://user:pass@localhost:27017/db`.
- `APP_POSTGRES_DSN` — `postgresql+asyncpg://user:pass@localhost:5432/db`.
- `APP_RABBITMQ_DSN` — `amqp://user:pass@localhost:5672/`.
- `APP_EVENTS_PING_INTERVAL_SECONDS` — keepalive interval for `/events` stream.

Connectors are created lazily and stored on `app.state` (`mongo`, `postgres`, `rabbitmq`). Dependency helpers live in `app/api/dependencies.py` for reuse in routes.

## Logging

`configure_logging` sets stdlib logging and structlog to emit JSON lines to stdout with level, timestamp, and tracebacks. Bind contextual fields with `get_logger(__name__).bind(...)`.

## CI

GitHub Actions workflow runs on pushes/PRs:
- `ruff check src tests`
- `pytest`
