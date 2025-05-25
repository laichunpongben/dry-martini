# martini/db.py

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Read database URL from environment
DATABASE_URL = os.getenv("POSTGRES_CONNECTION")
if not DATABASE_URL:
    raise RuntimeError("POSTGRES_CONNECTION is not set in environment variables")

# Swap in the asyncpg protocol if needed
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://", 1
    )
else:
    ASYNC_DATABASE_URL = DATABASE_URL  # assume user already provided async URL

# Async engine
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

# Async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Base class for ORM models
Base = declarative_base()