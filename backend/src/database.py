# database.py
import os

from fastapi import Depends
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import AsyncAdaptedQueuePool

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Configure engine with conservative pool settings for 2vCPU/4GB RAM
engine = create_async_engine(
    DATABASE_URL,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=5,  # Conservative pool size for 2vCPU
    max_overflow=5,  # Limited overflow for memory constraints
    pool_timeout=20,  # Shorter timeout to fail fast
    pool_recycle=1200,  # Recycle connections after 20 minutes
    pool_pre_ping=True,  # Enable connection health checks
    echo=False,  # Disable SQL echoing in production
    echo_pool=False,  # Disable pool logging in production
    future=True,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Better memory management
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()
