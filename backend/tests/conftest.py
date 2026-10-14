"""BlackBox — Pytest fixtures and database initialization."""
import pytest
from app.db.session import Base, engine


@pytest.fixture(autouse=True)
async def setup_test_database():
    """Ensure database tables exist before tests execute."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
