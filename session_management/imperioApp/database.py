"""
Database configuration for FastAPI
Using SQLAlchemy 2.0
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .utils.config import Config

# Create database engine
engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    **Config.SQLALCHEMY_ENGINE_OPTIONS
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    """
    Dependency function that yields database sessions.
    Use with FastAPI's Depends.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
