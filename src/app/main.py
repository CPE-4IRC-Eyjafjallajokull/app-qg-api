from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.routes import router as api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.security import KeycloakAuthenticator, KeycloakConfig
from app.services.db.postgres import PostgresManager
from app.services.events import SSEManager
from app.services.messaging.rabbitmq import RabbitMQManager
from app.services.messaging.subscriptions import ApplicationSubscriptions

configure_logging()
log = get_logger(__name__).bind(app=settings.app.name)

authenticator = KeycloakAuthenticator(KeycloakConfig.from_settings(settings))


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.authenticator = authenticator
    app.state.postgres = PostgresManager(settings.database)
    app.state.rabbitmq = RabbitMQManager(settings.rabbitmq)
    app.state.sse = SSEManager(
        heartbeat_interval=settings.app.events_ping_interval_seconds,
        queue_size=settings.app.events_queue_size,
        queue_overflow_strategy=settings.app.events_queue_overflow_strategy,
    )
    app.state.subscriptions = ApplicationSubscriptions(
        app.state.rabbitmq, app.state.sse
    )

    await app.state.postgres.connect()
    log.info("postgres.connected")
    await app.state.rabbitmq.connect()
    log.info("rabbitmq.connected")
    await app.state.subscriptions.start()
    log.info("rabbitmq.subscriptions.ready")

    log.info("startup.complete", env=settings.app.environment)
    try:
        yield
    finally:
        await app.state.subscriptions.stop()
        await app.state.sse.disconnect_all()
        await app.state.rabbitmq.close()
        await app.state.postgres.close()
        await app.state.authenticator.aclose()
        log.info("shutdown.complete")


app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    debug=False,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.state.authenticator = authenticator

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
register_exception_handlers(app)


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url=app.docs_url or "/docs")
