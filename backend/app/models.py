"""SQLAlchemy models. Source of design truth: docs/database-schema.md."""

from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    ARRAY,
    REAL,
    BigInteger,
    Boolean,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class Voie(TimestampMixin, Base):
    """Official named street from the Paris registry — the countable denominator."""

    __tablename__ = "voie"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    official_id: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    type: Mapped[str | None] = mapped_column(Text)
    arrondissements: Mapped[list[int] | None] = mapped_column(ARRAY(SmallInteger))
    quartier: Mapped[str | None] = mapped_column(Text)
    name_origin_fr: Mapped[str | None] = mapped_column(Text)
    name_history_fr: Mapped[str | None] = mapped_column(Text)
    included: Mapped[bool] = mapped_column(Boolean, default=True)
    exclusion_reason: Mapped[str | None] = mapped_column(Text)


class Segment(TimestampMixin, Base):
    """Matchable geometry from OSM. voie_id is null for park/cemetery paths."""

    __tablename__ = "segment"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    osm_way_id: Mapped[int | None] = mapped_column(BigInteger)
    voie_id: Mapped[int | None] = mapped_column(ForeignKey("voie.id"))
    kind: Mapped[str] = mapped_column(Text)  # street | park_path | cemetery_path | other
    geom = mapped_column(Geometry(geometry_type="LINESTRING", srid=4326))
    length_m: Mapped[float] = mapped_column(Float)
    included: Mapped[bool] = mapped_column(Boolean, default=True)
    exclusion_reason: Mapped[str | None] = mapped_column(Text)


class Walk(TimestampMixin, Base):
    """A chronicle entry — never an anonymous trace."""

    __tablename__ = "walk"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    strava_activity_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[str] = mapped_column(Text)
    walked_at: Mapped[datetime]
    distance_m: Mapped[int] = mapped_column(Integer)
    moving_time_s: Mapped[int] = mapped_column(Integer)
    steps: Mapped[int | None] = mapped_column(Integer)  # not generally exposed by Strava API
    with_kid: Mapped[bool] = mapped_column(Boolean, default=False)
    story_md: Mapped[str | None] = mapped_column(Text)
    trace_sha256: Mapped[str | None] = mapped_column(Text)
    trace_storage_url: Mapped[str | None] = mapped_column(Text)
    geom = mapped_column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=True)
    status: Mapped[str] = mapped_column(Text, default="ingested")  # ingested|matched|anchored


class WalkSegment(Base):
    """Coverage: which walk covered which segment, and how."""

    __tablename__ = "walk_segment"

    walk_id: Mapped[int] = mapped_column(ForeignKey("walk.id"), primary_key=True)
    segment_id: Mapped[int] = mapped_column(ForeignKey("segment.id"), primary_key=True)
    covered_fraction: Mapped[float] = mapped_column(REAL)
    method: Mapped[str] = mapped_column(Text)  # auto | manual
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Correction(Base):
    """The owner's auditable override. Never deleted; reversals are new rows."""

    __tablename__ = "correction"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    segment_id: Mapped[int] = mapped_column(ForeignKey("segment.id"))
    walk_id: Mapped[int | None] = mapped_column(ForeignKey("walk.id"))  # standalone allowed
    action: Mapped[str] = mapped_column(Text)  # mark_covered | reject
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Attestation(Base):
    """Proof of Walk: the on-chain anchor of a walk's raw trace."""

    __tablename__ = "attestation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    walk_id: Mapped[int] = mapped_column(ForeignKey("walk.id"), unique=True)
    sha256: Mapped[str] = mapped_column(Text)
    storage_provider: Mapped[str] = mapped_column(Text)  # placeholder: arweave
    storage_pointer: Mapped[str] = mapped_column(Text)
    chain: Mapped[str] = mapped_column(Text)
    tx_ref: Mapped[str] = mapped_column(Text)
    anchored_at: Mapped[datetime]


class Setting(Base):
    """Tunables. Initial: voie_completion_threshold = 0.9."""

    __tablename__ = "setting"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[str] = mapped_column(Text)
