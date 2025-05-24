# db.py

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from .env.local in project root
env_path = Path(__file__).parent.parent / ".env.local"
load_dotenv(dotenv_path=env_path)

# Now read the Postgres URL
DATABASE_URL = os.getenv("POSTGRES_CONNECTION")
if not DATABASE_URL:
    raise RuntimeError("POSTGRES_CONNECTION is not set in .env.local")

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
