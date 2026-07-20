# CLAUDE.md - Working Instructions

Read `PROJECT.md` first. It describes the project: the mission, the
architecture, the decisions, the vocabulary. This file tells you how to work
on it.

## How this project is being built

- **Phase 1:** vision and architecture defined in conversation on claude.ai;
  foundational documents and scaffold produced there.
- **Phase 2 (you, Claude Code):** long-run development inside this repo.
  `PROJECT.md` is your primary context; this file is your working contract.

## Build order

1. **Backend first.** The priority is a rock-solid foundation: PostGIS data
   model, Strava ingestion pipeline, map-matching, coverage computation,
   Proof of Walk anchoring. All technologies assembled and in harmony.
2. **UI can be ugly and basic in early iterations.** Do not spend effort on
   visual polish before the backend is solid.
3. **The facade comes last - and the bar is very high.** When the project
   reaches the look & feel phase, the owner has huge expectations: the site
   must be truly beautiful. Do not treat design as an afterthought when that
   phase arrives; treat it as a project of its own.

## Rules of the road

- **Decisions land in `PROJECT.md`, or they don't exist.** Any decision made
  in conversation, an issue, or a PR that changes vision, architecture, or
  scope must be reflected there. When a decision changes, the document
  changes with it.
- **No dogma.** Decisions in `PROJECT.md` are current best choices, not
  scripture. If life or inspiration makes a better case, propose the change -
  and record it.
- **The owner is the source of truth** - over GPS traces, over data sources,
  over defaults. When in doubt about scope or intent, ask; don't assume.
- Open questions are tracked in `PROJECT.md` §8. Don't silently resolve them
  in code; resolve them explicitly, then record the resolution.

## Engineering conventions

- TypeScript everywhere, strict mode.
- Monorepo: web app, ingestion worker, infra, chain package.
- Real-app discipline: CI must pass (typecheck, lint, tests) before merge;
  preview deploys on PRs; deploy on merge to main.
- The site is bilingual (EN/FR); do not hardcode user-facing strings.