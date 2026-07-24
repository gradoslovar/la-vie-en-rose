# Backend image: FastAPI + the in-process job consumer.
#
# Built by CI on every push (validation only, no registry push) and by Fly's
# remote builder on deploy.

FROM python:3.12-slim

# uv is pinned to an exact version, not `:latest`. A floating tag makes the
# build unreproducible and lets a compromised release land silently — the same
# reasoning applied to GitHub Actions in .claude/rules/ci-cd.md. Bump this
# deliberately.
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /usr/local/bin/uv

WORKDIR /app

# Dependencies in their own layer, before the application code: they change far
# less often, so this layer stays cached across most builds.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

# The virtualenv goes on PATH so the runtime does not need uv at all. This
# matters for more than tidiness: `uv run` wants a writable cache directory,
# which an unprivileged user may not have, and the container should not need
# one to start.
ENV PATH="/app/.venv/bin:$PATH"

# Runs unprivileged. .dockerignore keeps .env and the local virtualenv out of
# the image; this keeps a compromise inside the container from being root.
RUN groupadd --system --gid 1001 app \
 && useradd --system --uid 1001 --gid app app \
 && chown -R app:app /app
USER app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
