import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from app.core import health
from app.core.config import get_settings
from app.worker.runner import run_forever

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run the job consumer alongside the API.

    One machine serves requests and drains the queue. Jobs are durable in
    Postgres, so a restart mid-job loses nothing. Set WORKER_IN_PROCESS=false
    to run the worker as its own process instead.
    """
    task: asyncio.Task[None] | None = None
    if get_settings().worker_in_process:
        task = asyncio.create_task(run_forever())
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


app = FastAPI(
    title="la-vie-en-rose",
    description="Walking every street of Paris — API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
