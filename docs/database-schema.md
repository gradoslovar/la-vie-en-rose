# Database Schema — Design

Status: agreed design, pre-implementation. PostgreSQL + PostGIS. This document describes the data model; the migrations implementing it live in the repo and must stay consistent with it.

## Principles

- **Two-layer geography.** The official *voie* registry (Paris open data) is the countable denominator; OSM *segments* are the matchable geometry. A segment belongs to a voie when it represents a named street; park and cemetery paths are segments without a voie.
- **Coverage is recorded per segment, per walk.** A voie's "walked" status is always **derived**, never stored: a voie counts as walked when covered length ≥ threshold (default **0.9**, tunable via settings) of its included segments' total length. **We never store a `walked` boolean on the voie** — a stored flag drifts from the facts the moment the threshold changes, a correction lands, or data is re-imported. Derive, don't store.
- **The owner is the source of truth.** Editorial inclusion/exclusion and corrections are first-class, auditable records — never silent edits.
- **Replication is deliberate.** Strava essentials are copied into the DB (working copy for rendering/search/stats, and independence from Strava); the Strava activity link remains the social origin; the chain holds only proof (hash + pointers). Three copies, three roles.
- **Arrondissement membership is spatial, not typed by hand.** Which segment belongs to which arrondissement is resolved by PostGIS against the official arrondissement polygons (clipped at the boundary), so per-arrondissement stats are correct even for streets that straddle two.
- **No route-planning topology.** The app never plans or suggests routes (explicitly out of scope), so segments are plain LineStrings — no pgRouting node/edge graph. Deliberate: it would be permanent complexity for a case that will never exist.

## Tables

### `arrondissement` — a district as a first-class entity

Not just a tag: arrondissements have their own progress page, name, and stats.
Membership of segments is computed spatially against these polygons.

| column   | type                       | notes                                 |
|----------|----------------------------|---------------------------------------|
| number   | smallint PK                | 1–20                                  |
| name     | text                       | e.g. "Panthéon" (official name)       |
| geom     | geometry(MultiPolygon,4326)| boundary; GiST index                  |

### `voie` — the official named street

| column           | type            | notes                                    |
|------------------|-----------------|------------------------------------------|
| id               | bigint PK       |                                          |
| official_id      | text unique     | ID/code from Paris open data             |
| name             | text            | e.g. "Rue des Martyrs"                   |
| type             | text            | rue, avenue, boulevard, passage, impasse, villa, cité, place, quai, … |
| quartier         | text null       |                                          |
| name_origin_fr   | text null       | origin of the name (official source)     |
| name_history_fr  | text null       | historical notes (official source)       |
| included         | boolean default true | editorial: part of the mission?     |
| exclusion_reason | text null       | e.g. "bois", set when included = false   |
| created_at / updated_at | timestamptz |                                      |

### `segment` — matchable geometry (OSM)

| column        | type                        | notes                          |
|---------------|-----------------------------|--------------------------------|
| id            | bigint PK                   |                                |
| osm_way_id    | bigint                      | provenance                     |
| voie_id       | bigint FK null → voie       | null for park/cemetery paths   |
| arrondissement_number | smallint FK → arrondissement, null | set by spatial join; null if a segment falls outside the 20 (edge cases) |
| kind          | text                        | street, park_path, cemetery_path, other |
| geom          | geometry(LineString, 4326)  | GiST index; metric computations in Lambert-93 (EPSG:2154) |
| length_m      | double precision            | precomputed                    |
| included      | boolean default true        | editorial flag                 |
| exclusion_reason | text null                |                                |
| created_at / updated_at | timestamptz       |                                |

### `walk` — the chronicle entry

| column             | type          | notes                                |
|--------------------|---------------|--------------------------------------|
| id                 | bigint PK     |                                      |
| strava_activity_id | bigint unique | link back to Strava (social origin)  |
| name               | text          | e.g. "pa-chocolat" (`pa-` = Paris)   |
| walked_at          | timestamptz   |                                      |
| distance_m         | integer       | from Strava                          |
| moving_time_s      | integer       | from Strava                          |
| steps              | integer null  | not generally exposed by Strava API  |
| with_kid           | boolean       | from the Strava tag; filter + memories |
| story_md           | text null     | the walk's story, markdown           |
| trace_sha256       | text          | hash of the raw trace file           |
| trace_storage_url  | text          | app object storage (working copy)    |
| geom               | geometry(LineString, 4326) null | simplified trace for display |
| status             | text          | ingested → matched → anchored        |
| created_at / updated_at | timestamptz |                                   |

### `coverage` — which segment was covered, by what (formerly `walk_segment`)

Renamed from `walk_segment` because coverage can be **standalone** (a manual
correction with no walk attached). `walk_id` is nullable for exactly that case.

| column           | type          | notes                                     |
|------------------|---------------|-------------------------------------------|
| id               | bigint PK     | surrogate key (walk_id can be null)       |
| walk_id          | FK → walk, null | null = standalone manual coverage       |
| segment_id       | FK → segment  |                                           |
| covered_fraction | real          | 0–1, share of segment length matched      |
| method           | text          | `auto` (map-matching) or `manual` (correction) |
| created_at       | timestamptz   |                                           |

Uniqueness: at most one `auto` row per (walk_id, segment_id); manual rows are
reconciled from corrections. A `reject` correction suppresses an auto row in
the derived coverage (it is not physically deleted — history is preserved).

### `correction` — the owner's auditable override

| column     | type              | notes                                    |
|------------|-------------------|-------------------------------------------|
| id         | bigint PK         |                                           |
| segment_id | FK → segment      |                                           |
| walk_id    | FK → walk, null   | **walk-linked when possible; standalone as escape hatch** (null = "I know I walked this, don't remember which walk") |
| action     | text              | `mark_covered` or `reject`                |
| note       | text null         | why                                       |
| created_at | timestamptz       |                                           |

A `mark_covered` correction yields a `coverage` row with `method = manual` — attached to the walk when known, or standalone (`walk_id` null) for "I know I walked this, don't remember which walk." A `reject` correction suppresses the matching `auto` coverage in the derived views. Corrections are never deleted — reversals are new corrections. They are off-chain by design: the proof anchors raw traces; the editorial layer is visibly human.

### `attestation` — Proof of Walk

| column           | type          | notes                                  |
|------------------|---------------|-----------------------------------------|
| id               | bigint PK     |                                         |
| walk_id          | FK → walk, unique |                                     |
| sha256           | text          | of the anchored trace file              |
| storage_provider | text          | placeholder: arweave; not written in stone |
| storage_pointer  | text          |                                         |
| chain            | text          | open question (Solana vs EVM L2)        |
| tx_ref           | text          | transaction reference                   |
| anchored_at      | timestamptz   |                                         |

### `setting` — tunables

Key/value. Initial: `voie_completion_threshold = 0.9`.

## Derived (views / computed)

All "walked" status is derived from `coverage` (auto minus rejects, plus manual), never stored as a flag.

- **voie completion**: per voie, covered length of included segments / total included length; walked ⇔ ratio ≥ threshold.
- **headline progress**: walked voies / included voies; plus per-arrondissement (length-accurate thanks to `segment.arrondissement_number`).
- **effort stats**: Σ walk distance (total km) vs. Σ unique covered segment length (the overhead ratio — trivia, never a score).
- **kids' layer**: coverage restricted to walks where `with_kid = true`.

### Performance plan (materialized views)

Deriving completion on every map load would be wasteful at city scale. The intended path is **materialized views** — Postgres computes the derived result once and stores the *result* (never a status flag on the voie), refreshed when coverage changes (after ingestion or a correction). This keeps the single-source-of-truth guarantee while giving lookup-speed reads. Not in the first migration — added once there is real data to measure against, so we tune the refresh strategy on evidence rather than guesswork.

## Deliberately not modeled yet

Recommendations, photos/gallery, curated routes, practical layers (toilets, fountains, cool spots): future features, each gets its own design when its time comes.
