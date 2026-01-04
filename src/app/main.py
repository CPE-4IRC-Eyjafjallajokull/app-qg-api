from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from app.api.routes import router as api_router
from app.core.config import settings
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
    # Initialize managers
    app.state.authenticator = authenticator
    app.state.postgres = PostgresManager(settings.database)
    app.state.rabbitmq = RabbitMQManager(settings.rabbitmq)
    app.state.sse = SSEManager(
        heartbeat_interval=settings.app.events_ping_interval_seconds
    )
    app.state.subscriptions = ApplicationSubscriptions(
        app.state.rabbitmq, app.state.sse
    )

    # Ensure connections are established at startup
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
        # Graceful shutdown
        await app.state.subscriptions.stop()
        await app.state.sse.disconnect_all()
        await app.state.rabbitmq.close()
        await app.state.postgres.close()
        await app.state.authenticator.aclose()
        log.info("shutdown.complete")


app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    debug=settings.app.debug,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Expose authenticator immediately for dependencies (lifespan also keeps it in state).
app.state.authenticator = authenticator

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


# ---------------------------------------------------------------------------
# Global exception handlers - Return clean error messages, no tracebacks
# ---------------------------------------------------------------------------


def _extract_integrity_error_message(exc: IntegrityError) -> str:
    """Extract a user-friendly message from SQLAlchemy IntegrityError."""
    orig = str(exc.orig) if exc.orig else str(exc)

    # Foreign key violation
    if "ForeignKeyViolationError" in orig or "foreign key constraint" in orig.lower():
        # Try to extract table names from the error
        if "is still referenced from table" in orig:
            return "Cannot delete this resource because it is still referenced by related records. Please delete the related records first."
        if "is not present in table" in orig:
            return "Referenced resource does not exist. Please verify the related resource exists."
        return "Operation violates a foreign key constraint. Please check related resources."

    # Unique constraint violation
    if "UniqueViolationError" in orig or "unique constraint" in orig.lower():
        return "A resource with these values already exists. Please use unique values."

    # Not null violation
    if "NotNullViolationError" in orig or "not-null constraint" in orig.lower():
        return "A required field is missing. Please provide all required fields."

    # Check constraint violation
    if "CheckViolationError" in orig or "check constraint" in orig.lower():
        return "Data validation failed. Please verify the provided values."

    return "Database integrity constraint violated."


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors (foreign key, unique, etc.)."""
    log.warning(
        "database.integrity_error",
        path=request.url.path,
        method=request.method,
        error=str(exc.orig) if exc.orig else str(exc),
    )
    message = _extract_integrity_error_message(exc)
    return JSONResponse(
        status_code=409,
        content={"detail": message},
    )


@app.exception_handler(OperationalError)
async def operational_error_handler(request: Request, exc: OperationalError):
    """Handle database operational errors (connection, timeout, etc.)."""
    log.error(
        "database.operational_error",
        path=request.url.path,
        method=request.method,
        error=str(exc.orig) if exc.orig else str(exc),
    )
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database service temporarily unavailable. Please try again later."
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """Handle generic SQLAlchemy errors."""
    log.error(
        "database.error",
        path=request.url.path,
        method=request.method,
        error_type=type(exc).__name__,
        error=str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "A database error occurred. Please try again later."},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle any unhandled exceptions - prevent traceback leaks."""
    log.exception(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error_type=type(exc).__name__,
        error=str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url=app.docs_url or "/docs")
