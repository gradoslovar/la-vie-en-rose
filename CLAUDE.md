# CLAUDE.md — Working Instructions

Read `PROJECT.md` first. It describes the project: the mission, the architecture, the decisions, the vocabulary. This file tells you how to work on it.

## Where things are written down

| Document | What it holds |
|---|---|
| `PROJECT.md` | The mission, the architecture, the decisions, the vocabulary. Written in the owner's voice. |
| `CLAUDE.md` (this file) | How to work on the project. The index to everything else. |
| `docs/database-schema.md` | The data model and the reasoning behind it. |
| `docs/infrastructure.md` | What runs, where, why, and the accepted trade-offs. |
| `docs/testing.md` | What is tested, how, and what must pass before merge. |
| `.claude/rules/ci-cd.md` | Operational rules for CI, dependency updates, and deployment. |

`docs/` describes the system for any reader. `.claude/rules/` states rules you
must follow. Nothing is duplicated between them — when a rule needs context,
it links to the document rather than restating it.

## Decisions that need the owner's approval

Propose these and wait. Do not decide them and report afterwards:

- **Security posture** — permissions, secrets handling, access scopes, anything a workflow is allowed to write to.
- **Adding, removing, or changing dependencies and hosted services.**
- **Anything with a recurring cost.**
- **The content of documents written in the owner's voice** (`PROJECT.md`, `README.md`) — propose wording, do not author it.
- **Adding files to the repository that are not part of the project itself.**

When uncertain whether something clears this bar, ask. Asking is cheap; the
alternative is the owner discovering decisions instead of making them.

**Do not state facts about external services from memory.** Verify them, or say
plainly that the information is unverified. Fluent confidence about an
unchecked detail is worse than an admitted gap.

## How this project is being built

- **Phase 1:** vision and architecture defined in conversation on claude.ai; foundational documents and scaffold produced there.
- **Phase 2 (you, Claude Code):** long-run development inside this repo. `PROJECT.md` is your primary context; this file is your working contract.

## Build order

1. **Backend first.** The priority is a rock-solid foundation: PostGIS data model, Strava ingestion pipeline, map-matching, coverage computation, Proof of Walk anchoring. All technologies assembled and in harmony.
2. **UI can be ugly and basic in early iterations.** Do not spend effort on visual polish before the backend is solid.
3. **The facade comes last — and the bar is very high.** When the project reaches the look & feel phase, the owner has huge expectations: the site must be truly beautiful. Do not treat design as an afterthought when that phase arrives; treat it as a project of its own.

## Rules of the road

- **Decisions land in `PROJECT.md`, or they don't exist.** Any decision made in conversation, an issue, or a PR that changes vision, architecture, or scope must be reflected there. When a decision changes, the document changes with it.
- **No dogma.** Decisions in `PROJECT.md` are current best choices, not scripture. If life or inspiration makes a better case, propose the change — and record it.
- **The owner is the source of truth** — over GPS traces, over data sources, over defaults. When in doubt about scope or intent, ask; don't assume.
- Open questions are tracked in `PROJECT.md` §8. Don't silently resolve them in code; resolve them explicitly, then record the resolution.

## Engineering conventions

- **Backend: Python 3.12+, FastAPI.** uv for dependencies, ruff for lint/format, Pydantic v2, SQLAlchemy 2 + GeoAlchemy2 (raw SQL is welcome for serious PostGIS queries), Alembic for migrations, pytest.
- **Frontend: TypeScript strict, Next.js.** App Router. `next-intl` for EN/FR — no hardcoded user-facing strings, ever. MapLibre is loaded client-only (dynamic import, no SSR). Standalone output for Fly deploys.
- **The API contract is FastAPI's OpenAPI schema.** The typed TS client is generated from it — never hand-written, never hand-patched. CI verifies the generated client is in sync.
- Monorepo layout: `backend/` (API + worker + migrations), `frontend/`, `docs/`, `infra/`. These names are deliberately plain: `backend/` holds the API *and* the worker *and* the migrations, so `api/` would be a lie, and prefixing directories with the project name inside a repo already called `la-vie-en-rose` is noise.

## Backend layout

The backend is organised **by domain, not by technical role**, so a feature is readable by opening one folder rather than hunting across `routers/`, `services/`, and `schemas/`.

```
backend/app/
  main.py              app assembly only — no business logic
  core/                shared infrastructure: config, db session, models, health
  domains/
    geography/         arrondissements, voies, segments, data imports
    walks/             Strava ingestion, chronicle, coverage, corrections
    proof/             Proof of Walk: hashing, storage, anchoring, verification
    stats/             progress, breakdowns, effort metrics
  worker/              async jobs (ingestion, matching, anchoring)
```

- Within a domain, create `router.py`, `service.py`, `schemas.py` **as features land** — do not pre-create empty files.
- Domain boundaries come from the data model, not from imagination. If two domains start importing each other constantly, that is a signal the boundary is wrong: say so and propose merging them rather than adding indirection.
- `core/` is for genuinely shared infrastructure. Resist the temptation to park domain logic there because it's convenient.
- **Models stay in one file (`core/models.py`) until it hurts.** The whole data model on one scroll makes relationships legible, which matters more than file tidiness at this size. Split when the file exceeds roughly 500 lines or ~20 models — and split **by domain** (`geography.py`, `walks.py`, `proof.py`), not one file per table. If split, `__init__.py` must import every model so Alembic and the SQLAlchemy registry still see them.
- Real-app discipline: CI must pass (lint, types, tests) before merge; preview deploys on PRs; deploy on merge to main.
- The site is bilingual (EN/FR); do not hardcode user-facing strings.
