"""Shared test fixtures.

The database fixtures deliberately behave differently in CI and locally:

  * Locally, a developer without Postgres running gets skipped tests rather
    than a wall of connection errors.
  * In CI, REQUIRE_DB=1 turns that skip into a failure. A silently skipped
    database test is worse than no test — it reports green while proving
    nothing, which is exactly the gate hole this project's CI rules exist to
    prevent.
"""

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from app.core.config import get_settings


def _require_db() -> bool:
    return os.environ.get("REQUIRE_DB") == "1"


@pytest_asyncio.fixture
async def db() -> AsyncIterator[AsyncConnection]:
    """A live connection to a PostGIS database.

    Skips when no database is reachable, unless REQUIRE_DB=1.
    """
    engine = create_async_engine(get_settings().database_url)
    try:
        conn = await engine.connect()
    except Exception as exc:  # noqa: BLE001 - any connection failure is the same story
        await engine.dispose()
        if _require_db():
            pytest.fail(
                f"REQUIRE_DB=1 but the database is unreachable: {exc}. "
                "In CI this means the service container did not come up."
            )
        pytest.skip("no database available (start it with `docker compose up -d`)")
    try:
        yield conn
    finally:
        await conn.close()
        await engine.dispose()
