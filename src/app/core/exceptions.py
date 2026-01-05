"""Global exception handlers for the application."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from app.core.logging import get_logger

log = get_logger(__name__)


def _extract_integrity_error_message(exc: IntegrityError) -> str:
    """Extract a user-friendly message from SQLAlchemy IntegrityError."""
    orig = str(exc.orig) if exc.orig else str(exc)

    if "ForeignKeyViolationError" in orig or "foreign key constraint" in orig.lower():
        if "is still referenced from table" in orig:
            return "Cannot delete this resource because it is still referenced by related records."
        if "is not present in table" in orig:
            return "Referenced resource does not exist."
        return "Operation violates a foreign key constraint."

    if "UniqueViolationError" in orig or "unique constraint" in orig.lower():
        return "A resource with these values already exists."

    if "NotNullViolationError" in orig or "not-null constraint" in orig.lower():
        return "A required field is missing."

    if "CheckViolationError" in orig or "check constraint" in orig.lower():
        return "Data validation failed."

    return "Database integrity constraint violated."


async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    log.warning(
        "validation.request_error",
        path=request.url.path,
        method=request.method,
        errors=exc.errors(),
    )
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request data.", "errors": exc.errors()},
    )


async def pydantic_validation_error_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    log.error(
        "validation.response_error",
        path=request.url.path,
        method=request.method,
        error_count=exc.error_count(),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An error occurred while processing the response."},
    )


async def integrity_error_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    log.warning(
        "database.integrity_error",
        path=request.url.path,
        method=request.method,
        error=str(exc.orig) if exc.orig else str(exc),
    )
    return JSONResponse(
        status_code=409,
        content={"detail": _extract_integrity_error_message(exc)},
    )


async def operational_error_handler(
    request: Request, exc: OperationalError
) -> JSONResponse:
    log.error(
        "database.operational_error",
        path=request.url.path,
        method=request.method,
        error=str(exc.orig) if exc.orig else str(exc),
    )
    return JSONResponse(
        status_code=503,
        content={"detail": "Database service temporarily unavailable."},
    )


async def sqlalchemy_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    log.error(
        "database.error",
        path=request.url.path,
        method=request.method,
        error_type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "A database error occurred."},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.exception(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error_type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_error_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(OperationalError, operational_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
