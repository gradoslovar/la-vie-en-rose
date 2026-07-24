# Testing policy

What gets tested, how, and what must pass before code reaches `main`.

Written down deliberately early. Most of these categories are close to empty
today because the features they cover do not exist yet — the policy exists so
that when a feature lands, the tests that come with it are decided in advance
rather than improvised.

## The gate

`main` is protected. The `backend` and `frontend` CI checks must pass before a
pull request can merge. There is no path around this and no auto-merge for
anything, including dependency updates.

## Categories

### Unit tests — `backend/tests/`

Pure logic with no external dependencies: URL normalisation, parsing,
calculations. Fast, run always, no fixtures.

These will always be a minority in this project. Most of what it does is
database behaviour, and a unit test with a mocked database proves that the mock
behaves as written, which is nothing.

### Schema and database tests — `backend/tests/test_schema.py`, marked `db`

Run the real migration against a real PostGIS and assert the result. This is
the only thing that proves the schema works at all: the migration is
hand-written raw SQL, because Alembic's autogenerate mangles geometry columns
and partial indexes.

Asserted today: PostGIS installed, every expected table present, geometry
columns carry the right type and SRID, the GiST index exists, `coverage.walk_id`
is nullable (the standalone-correction escape hatch), the completion threshold
is seeded.

**Kept in step with `docs/database-schema.md`.** A table, index or constraint
added there is asserted here in the same change.

### Integration tests — as features land

The important category for this project, and currently empty because the
features are not built. Everything that matters is database behaviour:

- **Map-matching**: a known trace against a known street network produces the
  expected covered segments and fractions. This is where GPS drift, the thing
  the whole project exists to correct, either works or does not.
- **Coverage and completion**: derived voie status against the threshold,
  including a voie straddling two arrondissements contributing its real metres
  to each.
- **Corrections**: a `mark_covered` produces manual coverage; a `reject`
  suppresses an auto match; a standalone correction works with no walk;
  reversals are new rows and history is never deleted.
- **Ingestion**: a fixture Strava payload through the pipeline, including the
  `pa-` filter and the "With Kid" tag.
- **Proof of Walk**: hash stability, and verification against a stored trace.

These use real fixture data — a small extract of the Paris network and a real
GPX trace — not mocks.

### End-to-end tests — not yet

No UI exists beyond a placeholder. Playwright before then would be theatre.

Adopt when the map is real. First candidates: the map loads and renders walked
segments; language switching works; a walk page shows its chronicle entry and
its proof.

## Rules

**A database test that skips is a failure in CI.** `tests/conftest.py` skips
when no database is reachable so local runs without Postgres are usable, but
`REQUIRE_DB=1` — set in CI — turns that skip into a hard failure. A silently
skipped database test reports green while proving nothing.

**Migrations are applied twice in CI.** Deploys run migrations on every
release; one that fails on second application is a broken deploy waiting to
happen.

**No coverage percentage target.** A number invites tests written to raise the
number. The rule instead: a feature is not done until its behaviour is tested,
and a bug fix comes with the test that would have caught it.

**Fixtures over mocks for anything spatial.** A mocked PostGIS proves nothing
about PostGIS.

## Running locally

```bash
docker compose up -d                    # PostGIS on :5432
cd backend
uv sync
uv run alembic upgrade head
uv run pytest                           # db tests skip if Postgres is down
uv run pytest -m db                     # only the database tests
REQUIRE_DB=1 uv run pytest              # fail instead of skip, as CI does
```
