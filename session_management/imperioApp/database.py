"""
Database configuration for FastAPI with async SQLite
Using SQLAlchemy 2.0 with aiosqlite
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .utils.config import Config

# Create async database engine for SQLite
DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', 'sqlite+aiosqlite:///')

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

# Create async session maker
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create Base class for models
Base = declarative_base()

# Dependency to get async database session
async def get_async_db():
    """
    Async dependency function that yields database sessions.
    Use with FastAPI's Depends.
    """
    async with async_session_maker() as session:
        yield session
