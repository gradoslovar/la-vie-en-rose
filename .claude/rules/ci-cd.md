# CI/CD rules

Operational rules for continuous integration, dependency updates, and
deployment. Follow these; do not relitigate them silently. When one is wrong,
say so and propose the change.

Reference documents: `docs/infrastructure.md` (what runs and why),
`docs/testing.md` (what is tested).

## The gate

`main` is protected. Required checks: **`backend`** and **`frontend`**.

**Never rename or split a CI job without updating branch protection in the same
change.** Protection waits for an exact context name. A renamed job means
protection waits forever for a check that will never report, and nothing can
merge.

## CI

`.github/workflows/ci.yml`. Runs on every push to `main` and every pull request.

**No path filters. Ever.** They look like a free speed win and are a gate hole:
GitHub counts a skipped job as green, so a changed file matching no filter means
every gated job skips and the pull request merges having run nothing at all.
Every push runs everything. This project is small; correctness is worth more
than the saved minutes.

**The backend job has a PostGIS service container, and that is the point of
it.** Without a database, ruff and a few unit tests pass while the schema, the
migration and every spatial query go unexercised — a dependency bump that broke
database behaviour would report green. The image is `postgis/postgis:16-3.4`,
matching production and local development exactly.

**`REQUIRE_DB=1` is set in CI and must stay set.** It converts "no database,
skipping" into a hard failure. Without it, a broken service container produces a
green run full of skips.

**Migrations are applied twice.** The second application must be a no-op.
Deploys run migrations on every release.

Checks in order: ruff lint, ruff format, pyright, migrate, migrate again, pytest.

Pyright runs in `standard` mode, not `strict`. GeoAlchemy2's type information is
incomplete and strict reports correct schema code as errors — a type checker
whose output must be ignored is worse than none.

## Dependabot

`.github/dependabot.yml`. Weekly, Monday, three ecosystems.

**Nothing is auto-merged, including patches.** Auto-merge is a legitimate
practice and published guidance moved away from it during the 2026 supply-chain
attacks. It also requires a workflow with write access to the repository, which
the owner has declined. Revisit only when the test suite is substantial enough
to trust as a gate — and ask first.

**Everything is grouped, and majors are never grouped with anything.** An
earlier ungrouped configuration produced six pull requests in two days for a
repository with about two hundred lines of code. The benchmark to hold: fewer
than five dependency pull requests per week. More than that is a configuration
bug, not a fact of life. Majors arrive individually because they break things
and need a changelog read.

**The 3-day cooldown stays.** No update is proposed until it has been public for
three days, so a compromised or mistaken release has time to be caught.
Security updates are not governed by the schedule and arrive immediately.

**Security alerts, malware alerts, and grouped security updates are repository
settings, not this file.** Do not assume they are on; they are, but check rather
than assert.

## Dependency review

`.github/workflows/dependency-review.yml`. Blocks pull requests that introduce a
vulnerable or wrongly-licensed dependency. Available because the repository is
public.

`fail-on-severity: moderate` — `low` blocks on transitive advisories that often
have no fix available, and a gate that blocks with no remedy gets switched off.

`fail-on-scopes: runtime` — a vulnerability in ruff or pytest ships nowhere, and
blocking on it would contradict the repository's enabled Dependabot preset,
which already dismisses development-scoped alerts.

The license list is an **allow-list** (`deny-licenses` is deprecated for
removal). Notable exclusion: **AGPL**, whose obligations trigger on network use
— exactly this project's situation as a hosted public site. A legitimate
dependency under an unlisted license will fail this check; that is intended. Add
the license deliberately, having read it.

**This is not a required check yet.** Adding it to branch protection is a manual
step and has not been done.

## Actions

**Latest major version tag, kept current by Dependabot.** In use:
`actions/checkout@v7`, `actions/setup-node@v7`, `astral-sh/setup-uv@v9`,
`actions/dependency-review-action@v5`, `superfly/flyctl-actions/setup-flyctl@1.5`.

**Never a branch reference.** `@master` or `@main` is not a version — it means CI
runs whatever that branch contains today. The Fly action was on `@master` until
it was pinned to a release; do not put it back.

Commit-SHA pinning was considered and **declined**: a tag is a mutable pointer
the action's owner can repoint at any commit, which is how the
`tj-actions/changed-files` compromise leaked secrets from thousands of
repositories in 2025 — but the readability cost was judged not worth it here.
This is a live trade-off, not a settled fact. If it is revisited, Dependabot
maintains SHAs just as happily.

## Comments in configuration files

**Every workflow and configuration file carries its own reasoning.** Not
narration of what a step does — the reason it exists, what breaks without it,
and what must not be undone.

A comment saying "installs dependencies" is worthless. A comment saying "`npm ci`
not `npm install`, because it fails when package.json and the lockfile disagree,
and that disagreement is a real failure mode of dependency pull requests" is
institutional memory. Write the second kind.

The test: if a decision here were reversed six months from now by someone who
was not in the conversation, would the file tell them why they should not?

## Deployment

`docs/infrastructure.md` is the reference. Rules that live here:

**No command is run from a personal machine.** Every infrastructure action is a
workflow. If something needs doing by hand, that is a gap — add a workflow
instead of documenting an incantation. Lockfile generation is the
deliberate exception: it is ordinary development, not infrastructure, and
automating it would require giving a workflow write access to the repository,
which the owner has declined.

**Nothing has been deployed yet.** The deploy, provision, backup, restore, and
scale workflows have never run. Treat them as unverified until they have.
