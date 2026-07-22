"""Feature domains.

Each domain owns one concept end to end: its routes, its business logic, and
its Pydantic schemas. A feature should be readable by opening one folder.

- geography: arrondissements, voies, segments, data imports (OSM, Paris open data)
- walks:     Strava ingestion, the chronicle, coverage, corrections
- proof:     Proof of Walk — hashing, permanent storage, chain anchoring, verification
- stats:     progress, per-arrondissement breakdowns, effort metrics

Convention per domain (create files as features land, not before):
    router.py    FastAPI routes
    service.py   business logic
    schemas.py   Pydantic request/response models
"""
