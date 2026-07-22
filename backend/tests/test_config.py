import pytest

from app.core.config import Settings


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        # Fly injects this form when attaching Managed Postgres.
        ("postgres://u:p@host:5432/db", "postgresql+asyncpg://u:p@host:5432/db"),
        ("postgresql://u:p@host:5432/db", "postgresql+asyncpg://u:p@host:5432/db"),
        # Already explicit — left alone.
        ("postgresql+asyncpg://u:p@host:5432/db", "postgresql+asyncpg://u:p@host:5432/db"),
    ],
)
def test_database_url_gets_async_driver(given: str, expected: str) -> None:
    assert Settings(database_url=given).database_url == expected
