from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.services.db.mongo import MongoClientManager
from app.services.db.postgres import PostgresManager
from app.services.messaging.rabbitmq import RabbitMQManager

configure_logging(settings.log_level)
log = get_logger(__name__).bind(app=settings.app_name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo = MongoClientManager(settings)
    app.state.postgres = PostgresManager(settings)
    app.state.rabbitmq = RabbitMQManager(settings)
    log.info("startup.complete", env=settings.environment)
    try:
        yield
    finally:
        await app.state.rabbitmq.close()
        await app.state.postgres.close()
        await app.state.mongo.close()
        log.info("shutdown.complete")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.include_router(api_router)
