# Database Schema — Design

Status: agreed design, pre-implementation. PostgreSQL + PostGIS.
This document describes the data model; the migrations implementing it live
in the repo and must stay consistent with it.

## Principles

- **Two-layer geography.** The official *voie* registry (Paris open data) is
  the countable denominator; OSM *segments* are the matchable geometry. A
  segment belongs to a voie when it represents a named street; park and
  cemetery paths are segments without a voie.
- **Coverage is recorded per segment, per walk.** A voie's "walked" status is
  always **derived**, never stored: a voie counts as walked when covered
  length ≥ threshold (default **0.9**, tunable via settings) of its included
  segments' total length.
- **The owner is the source of truth.** Editorial inclusion/exclusion and
  corrections are first-class, auditable records — never silent edits.
- **Replication is deliberate.** Strava essentials are copied into the DB
  (working copy for rendering/search/stats, and independence from Strava);
  the Strava activity link remains the social origin; the chain holds only
  proof (hash + pointers). Three copies, three roles.

## Tables

### `voie` — the official named street

| column           | type            | notes                                    |
|------------------|-----------------|------------------------------------------|
| id               | bigint PK       |                                          |
| official_id      | text unique     | ID/code from Paris open data             |
| name             | text            | e.g. "Rue des Martyrs"                   |
| type             | text            | rue, avenue, boulevard, passage, impasse, villa, cité, place, quai, … |
| arrondissements  | smallint[]      | a voie can cross several                 |
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

### `walk_segment` — coverage (which walk covered what)

| column           | type      | notes                                     |
|------------------|-----------|-------------------------------------------|
| walk_id          | FK → walk | PK (walk_id, segment_id)                  |
| segment_id       | FK → segment |                                        |
| covered_fraction | real      | 0–1, share of segment length matched      |
| method           | text      | `auto` (map-matching) or `manual` (correction) |
| created_at       | timestamptz |                                         |

### `correction` — the owner's auditable override

| column     | type              | notes                                    |
|------------|-------------------|-------------------------------------------|
| id         | bigint PK         |                                           |
| segment_id | FK → segment      |                                           |
| walk_id    | FK → walk, null   | **walk-linked when possible; standalone as escape hatch** (null = "I know I walked this, don't remember which walk") |
| action     | text              | `mark_covered` or `reject`                |
| note       | text null         | why                                       |
| created_at | timestamptz       |                                           |

A `mark_covered` correction produces/updates a `walk_segment` row with
`method = manual` (or, when standalone, a coverage row attached to no walk —
modeled with a nullable walk reference in coverage or a dedicated derived
view; to be settled at migration time, the semantics above are what counts).
A `reject` removes an auto match from the derived coverage. Corrections are
never deleted — reversals are new corrections. Corrections are off-chain by
design: the proof anchors raw traces; the editorial layer is visibly human.

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

- **voie completion**: per voie, covered length of included segments
  (union of auto + manual coverage, minus rejects) / total included length;
  walked ⇔ ratio ≥ threshold.
- **headline progress**: walked voies / included voies; plus per-arrondissement.
- **effort stats**: Σ walk distance (total km) vs. Σ unique covered segment
  length (the overhead ratio — trivia, never a score).
- **kids' layer**: coverage restricted to walks where `with_kid = true`.

## Deliberately not modeled yet

Recommendations, photos/gallery, curated routes, practical layers (toilets,
fountains, cool spots): future features, each gets its own design when its
time comes.
