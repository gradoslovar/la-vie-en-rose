"""Verifies the migration produced the schema the design document describes.

This is the only test that proves the schema works at all. The migration is
hand-written raw SQL (deliberately — Alembic's autogenerate mangles PostGIS
geometry columns and partial indexes), so nothing else validates it.

Kept in step with docs/database-schema.md: if a table, index or constraint is
added there, it is asserted here.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

pytestmark = pytest.mark.db

EXPECTED_TABLES = {
    "alembic_version",
    "arrondissement",
    "attestation",
    "correction",
    "coverage",
    "segment",
    "setting",
    "voie",
    "walk",
}


async def test_postgis_is_installed(db: AsyncConnection) -> None:
    """Without PostGIS this project cannot exist, so assert it explicitly."""
    result = await db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'postgis'"))
    assert result.scalar() == "postgis"


async def test_expected_tables_exist(db: AsyncConnection) -> None:
    result = await db.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    )
    tables = {row[0] for row in result}
    missing = EXPECTED_TABLES - tables
    assert not missing, f"migration did not create: {sorted(missing)}"


async def test_segment_geometry_column_is_typed(db: AsyncConnection) -> None:
    """A geometry column that lost its type or SRID silently breaks every
    spatial query, so both are asserted rather than assumed."""
    result = await db.execute(
        text("""
            SELECT type, srid FROM geometry_columns
            WHERE f_table_name = 'segment' AND f_geometry_column = 'geom'
        """)
    )
    row = result.first()
    assert row is not None, "segment.geom is not registered as a geometry column"
    assert row[0] == "LINESTRING"
    assert row[1] == 4326


async def test_spatial_index_exists(db: AsyncConnection) -> None:
    """Coverage queries scan segment geometry. Without the GiST index this
    works correctly and unusably slowly, which no other test would catch."""
    result = await db.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = 'segment'"))
    indexes = {row[0] for row in result}
    assert "ix_segment_geom" in indexes


async def test_coverage_allows_standalone_manual_rows(db: AsyncConnection) -> None:
    """A correction with no walk attached is the owner's escape hatch: "I know
    I walked this, I don't remember which walk." The nullable walk_id is the
    whole reason `coverage` replaced the old `walk_segment` table, so it is
    asserted rather than trusted."""
    result = await db.execute(
        text("""
            SELECT is_nullable FROM information_schema.columns
            WHERE table_name = 'coverage' AND column_name = 'walk_id'
        """)
    )
    assert result.scalar() == "YES"


async def test_completion_threshold_is_seeded(db: AsyncConnection) -> None:
    """A voie counts as walked at this fraction of its length. The default is
    0.9 so a clipped metre at an intersection does not hold a street hostage."""
    result = await db.execute(
        text("SELECT value FROM setting WHERE key = 'voie_completion_threshold'")
    )
    assert result.scalar() == "0.9"
