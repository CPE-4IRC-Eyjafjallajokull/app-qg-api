from typing import AsyncIterator

from aio_pika.abc import AbstractRobustConnection
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import AuthenticatedUser
from app.core.security.keycloak import KeycloakAuthenticator
from app.services.db.postgres import PostgresManager
from app.services.events import SSEManager
from app.services.messaging.rabbitmq import RabbitMQManager

bearer_scheme = HTTPBearer(auto_error=False)


async def get_postgres_session(request: Request) -> AsyncIterator[AsyncSession]:
    manager: PostgresManager = request.app.state.postgres
    async for session in manager.get_session():
        yield session


async def get_rabbitmq_connection(request: Request) -> AbstractRobustConnection:
    manager: RabbitMQManager = request.app.state.rabbitmq
    return await manager.get_connection()


def get_rabbitmq_manager(request: Request) -> RabbitMQManager:
    """Get the RabbitMQ manager for publishing/consuming messages."""
    return request.app.state.rabbitmq


def get_sse_manager(request: Request) -> SSEManager:
    """Get the SSE manager for broadcasting events to connected clients."""
    return request.app.state.sse


async def get_authenticator(request: Request) -> KeycloakAuthenticator:
    return request.app.state.authenticator


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    authenticator: KeycloakAuthenticator = Depends(get_authenticator),
) -> AuthenticatedUser:
    """Validate the bearer token and return the authenticated user."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await authenticator.authenticate(token)
