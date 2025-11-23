"""
Authentication API routes using FastAPI-Users
Replaces custom JWT authentication
"""
from fastapi import APIRouter, Depends
from fastapi_users import schemas
from ..utils.users import fastapi_users, auth_backend
from ..utils.models_users import User
import uuid
from pydantic import BaseModel, EmailStr


# Pydantic schemas for FastAPI-Users
class UserRead(schemas.BaseUser[uuid.UUID]):
    """Schema for reading user data"""
    username: str
    coins: int


class UserCreate(schemas.BaseUserCreate):
    """Schema for creating a user"""
    username: str
    email: EmailStr
    password: str


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating user data"""
    username: str | None = None
    coins: int | None = None


# Create router
router = APIRouter()

# Include FastAPI-Users authentication routes
# This creates: /auth/jwt/login, /auth/jwt/logout, /auth/register, etc.
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["Authentication"]
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["Authentication"]
)

router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["Authentication"]
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["Authentication"]
)

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["Users"]
)
