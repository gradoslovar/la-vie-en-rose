"""Initial schema — implements docs/database-schema.md.

Revision ID: 0001
Revises:
Create Date: 2026-07-20
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.execute("""
        CREATE TABLE arrondissement (
            number SMALLINT PRIMARY KEY,
            name TEXT NOT NULL,
            geom geometry(MultiPolygon, 4326) NOT NULL
        )
    """)
    op.execute("CREATE INDEX ix_arrondissement_geom ON arrondissement USING GIST (geom)")

    op.execute("""
        CREATE TABLE voie (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            official_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            type TEXT,
            quartier TEXT,
            name_origin_fr TEXT,
            name_history_fr TEXT,
            included BOOLEAN NOT NULL DEFAULT TRUE,
            exclusion_reason TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE segment (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            osm_way_id BIGINT,
            voie_id BIGINT REFERENCES voie(id),
            arrondissement_number SMALLINT REFERENCES arrondissement(number),
            kind TEXT NOT NULL,
            geom geometry(LineString, 4326) NOT NULL,
            length_m DOUBLE PRECISION NOT NULL,
            included BOOLEAN NOT NULL DEFAULT TRUE,
            exclusion_reason TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_segment_geom ON segment USING GIST (geom)")
    op.execute("CREATE INDEX ix_segment_voie ON segment (voie_id)")
    op.execute("CREATE INDEX ix_segment_arr ON segment (arrondissement_number)")

    op.execute("""
        CREATE TABLE walk (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            strava_activity_id BIGINT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            walked_at TIMESTAMPTZ NOT NULL,
            distance_m INTEGER NOT NULL,
            moving_time_s INTEGER NOT NULL,
            steps INTEGER,
            with_kid BOOLEAN NOT NULL DEFAULT FALSE,
            story_md TEXT,
            trace_sha256 TEXT,
            trace_storage_url TEXT,
            geom geometry(LineString, 4326),
            status TEXT NOT NULL DEFAULT 'ingested',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_walk_walked_at ON walk (walked_at)")

    op.execute("""
        CREATE TABLE coverage (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            walk_id BIGINT REFERENCES walk(id),
            segment_id BIGINT NOT NULL REFERENCES segment(id),
            covered_fraction REAL NOT NULL,
            method TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT covered_fraction_range
                CHECK (covered_fraction >= 0 AND covered_fraction <= 1),
            CONSTRAINT method_values CHECK (method IN ('auto', 'manual'))
        )
    """)
    op.execute("CREATE INDEX ix_coverage_segment ON coverage (segment_id)")
    op.execute("CREATE INDEX ix_coverage_walk ON coverage (walk_id)")
    # one auto match per (walk, segment); manual rows may repeat / be standalone
    op.execute("""
        CREATE UNIQUE INDEX ux_coverage_auto ON coverage (walk_id, segment_id)
        WHERE method = 'auto'
    """)

    op.execute("""
        CREATE TABLE correction (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            segment_id BIGINT NOT NULL REFERENCES segment(id),
            walk_id BIGINT REFERENCES walk(id),
            action TEXT NOT NULL,
            note TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT action_values CHECK (action IN ('mark_covered', 'reject'))
        )
    """)

    op.execute("""
        CREATE TABLE attestation (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            walk_id BIGINT NOT NULL UNIQUE REFERENCES walk(id),
            sha256 TEXT NOT NULL,
            storage_provider TEXT NOT NULL,
            storage_pointer TEXT NOT NULL,
            chain TEXT NOT NULL,
            tx_ref TEXT NOT NULL,
            anchored_at TIMESTAMPTZ NOT NULL
        )
    """)

    op.execute("""
        CREATE TABLE setting (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    op.execute("INSERT INTO setting (key, value) VALUES ('voie_completion_threshold', '0.9')")


def downgrade() -> None:
    for table in (
        "attestation",
        "correction",
        "coverage",
        "walk",
        "segment",
        "voie",
        "arrondissement",
        "setting",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table}")
