"""
FastAPI-Users authentication configuration
Replaces custom JWT authentication with FastAPI-Users
"""
import uuid
from typing import Optional, AsyncGenerator
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from .models_users import User
from ..database import get_async_db
from .config import Config
import logging

logger = logging.getLogger(__name__)


async def get_user_db(session: AsyncSession = Depends(get_async_db)) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    """Get user database adapter for FastAPI-Users"""
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """User manager for FastAPI-Users"""
    reset_password_token_secret = Config.SECRET_KEY
    verification_token_secret = Config.SECRET_KEY

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """Called after user registration"""
        logger.info(f"User {user.id} has registered")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Called after forgot password request"""
        logger.info(f"User {user.id} requested password reset")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Called after verification request"""
        logger.info(f"Verification requested for user {user.id}")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """Dependency to get user manager"""
    yield UserManager(user_db)


# Configure JWT authentication
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    """Get JWT strategy for authentication"""
    return JWTStrategy(
        secret=Config.SECRET_KEY,
        lifetime_seconds=Config.ACCESS_TOKEN_EXPIRE_HOURS * 3600,  # Convert hours to seconds
        algorithm=Config.ALGORITHM
    )


# Create authentication backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# Create FastAPI-Users instance
fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

# Export commonly used dependencies
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
