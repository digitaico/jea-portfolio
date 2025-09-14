"""
Shared Database Module
Provides database connection, session management, and base models for all services.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean
from typing import AsyncGenerator, Optional
import os
from datetime import datetime

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://healthcare_user:healthcare_pass@localhost:5432/healthcare_db")

# Create engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging in development
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
)

# Create async session factory
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Base class for all models
Base = declarative_base()

class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True

    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session.
    Use in FastAPI route handlers: db: AsyncSession = Depends(get_db)
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_database():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_database():
    """Close database connections"""
    await engine.dispose()

# Common database utilities
async def commit_and_refresh(session: AsyncSession, instance):
    """Commit transaction and refresh instance"""
    await session.commit()
    await session.refresh(instance)

async def add_and_commit(session: AsyncSession, instance):
    """Add instance and commit transaction"""
    session.add(instance)
    await session.commit()
    await session.refresh(instance)