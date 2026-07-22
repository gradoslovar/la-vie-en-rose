# Infrastructure

Status: agreed design. Everything here is executed by GitHub Actions — no
command is ever run from a personal machine. The repository is the only place
infrastructure is defined or changed.

## What runs

Three Fly.io apps in **`ams`** (Amsterdam), all in the same region so the app
and its database are co-located.

| App | What it is | Machines |
|---|---|---|
| `lvr-db` | PostgreSQL 16 + PostGIS, official `postgis/postgis` image, one volume | 1 |
| `lvr-backend` | FastAPI + the in-process job consumer | 1 |
| `lvr-frontend` | Next.js | 1 |

Amsterdam rather than Paris because managed Postgres has no CDG region and the
region choice should stay consistent if we ever migrate. "Hosted in Paris" was
romance; co-location is substance.

## Decisions and their trade-offs

### Self-managed Postgres, not Managed Postgres

Managed Postgres buys convenience rather than capability, and the site is not
widely visited during the mission. Self-managed is the current choice.

Accepted consequences: single node, no automatic failover, we own version
upgrades, and nobody is on call. The site being briefly down is not a problem
at this stage.

Mitigation is not optional: **backups are automated and verified nightly**
(below). The reason to fear self-management is data loss, and that is answered
directly rather than by paying to avoid the question.

**The migration path is preserved deliberately.** When the site opens to a
broader audience, moving to MPG is a `pg_dump` / `pg_restore` — nothing in the
schema, the app, or the queries is specific to how Postgres is hosted.

### Not `fly postgres create`

Fly's own Postgres image **does not ship PostGIS**, which this project cannot
exist without. Rather than fork and maintain Fly's `postgres-flex` image, we run
an ordinary Fly app on the upstream `postgis/postgis` image with a volume. The
image is maintained by the PostGIS project, and what runs is stock Postgres —
which is exactly what keeps the migration path to MPG open.

We lose `fly postgres` conveniences (we do not need them) and repmgr-based HA
(not needed at this stage).

### One backend machine, worker in-process

The job consumer runs as a background task inside the API process. Jobs live in
a **durable Postgres queue**, so a restart mid-job loses nothing: pending work
is picked up on boot.

Why not a separate worker machine: walks happen roughly once a day. Ingestion is
rare and bursty. A dedicated always-on machine to wait for it is over-provisioned
for the actual workload.

Accepted consequence: matching shares CPU with the API. Irrelevant at this
traffic; during a large backfill the API will feel sluggish for a few minutes.

**The promotion path is kept free**: the consumer lives in `app/worker/runner.py`
with its own entrypoint (`python -m app.worker`). Moving it to a dedicated Fly
process group is a config change — set `WORKER_IN_PROCESS=false` and add a
`[processes]` block — not a rewrite.

### No scale-to-zero anywhere

Machine count is an explicit decision made through `.github/workflows/scale.yml`,
not an automatic reaction to traffic. The backend could not scale to zero anyway
(it consumes a queue, and an idle-looking machine would be stopped mid-job), and
the owner prefers deliberate control over the rest.

## Workflows

| Workflow | Trigger | What it does |
|---|---|---|
| `ci.yml` | push to main, PRs | lint, format check, tests, frontend typecheck + build |
| `provision.yml` | manual | creates apps, volume, and backup bucket — idempotent |
| `deploy.yml` | merge to main | deploys db → backend → frontend, verifies health |
| `backup.yml` | nightly 03:17 UTC | dump, **verify it restores**, upload, prune >90 days |
| `restore.yml` | manual + confirmation | restores a chosen backup over the live database |
| `scale.yml` | manual | sets machine count per app (0 stops it) |

Deploy order matters: the database is deployed first, so the backend never
starts against an older schema. Migrations run through `release_command` in
`fly.backend.toml`, before the new version takes traffic.

### Backups are verified, not assumed

`backup.yml` restores every dump into a scratch PostGIS container before
uploading it. A backup that has never been restored is not a backup — and since
Postgres is self-managed here, the backup being real is what makes that choice
defensible.

Retention: 90 days of nightly dumps in Tigris object storage.

## Required GitHub secrets

| Secret | Purpose |
|---|---|
| `FLY_API_TOKEN` | deploy and administer Fly apps |
| `POSTGRES_PASSWORD` | database password (also set as a Fly secret on `lvr-db`) |
| `TIGRIS_ACCESS_KEY_ID` | backup storage |
| `TIGRIS_SECRET_ACCESS_KEY` | backup storage |

`DATABASE_URL` is not stored by hand: `provision.yml` composes it and stages it
as a Fly secret on `lvr-backend`. The backend normalises Fly's `postgres://`
form to the asyncpg driver at startup (`app/core/config.py`).

## Connecting to the database

`lvr-db` is not exposed to the public internet. It is reachable as
`lvr-db.internal:5432` on Fly's private network, and from CI through
`flyctl proxy`. Local development uses the `docker compose` Postgres, which runs
the same `postgis/postgis` image as production.

