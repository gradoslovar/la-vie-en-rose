"""Ingestion worker package.

Will host: Strava webhook processing, map-matching jobs, Proof of Walk
anchoring. Queue: Postgres-based (no extra broker), to be wired when the
ingestion feature lands.
"""
