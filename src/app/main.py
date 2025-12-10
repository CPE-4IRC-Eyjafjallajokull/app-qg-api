from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.services.db.postgres import PostgresManager
from app.services.events import SSEManager
from app.services.messaging.rabbitmq import RabbitMQManager

configure_logging(settings.log_level)
log = get_logger(__name__).bind(app=settings.app_name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize managers
    app.state.postgres = PostgresManager(settings)
    app.state.rabbitmq = RabbitMQManager(settings)
    app.state.sse = SSEManager(heartbeat_interval=settings.events_ping_interval_seconds)

    # Ensure connections are established at startup
    await app.state.postgres.connect()
    log.info("postgres.connected")
    await app.state.rabbitmq.connect()
    log.info("rabbitmq.connected")

    log.info("startup.complete", env=settings.environment)
    try:
        yield
    finally:
        # Graceful shutdown
        await app.state.sse.disconnect_all()
        await app.state.rabbitmq.close()
        await app.state.postgres.close()
        log.info("shutdown.complete")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
