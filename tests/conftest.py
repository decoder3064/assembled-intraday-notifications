import os

# Must be set before anything imports app.persistence.database, since the
# engine is created at import time. Tests get their own database so running
# the suite can never wipe a real dev/demo session's data again.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://app:app@localhost:5433/notifications_test")

import pytest_asyncio

from app.persistence.database import async_session, engine
from app.persistence.models import Base


@pytest_asyncio.fixture
async def clean_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(clean_db):
    async with async_session() as session:
        yield session
        await session.rollback()
