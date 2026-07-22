"""The job consumer.

Runs in-process alongside the API today (see app/main.py lifespan). The jobs
themselves live in a durable Postgres queue, so nothing is lost if the machine
restarts mid-job — pending work is picked up again on boot.

This module is deliberately independent of the API. If map-matching ever grows
heavy enough to compete with request latency, it is promoted to its own Fly
process group by running `python -m app.worker` and flipping WORKER_IN_PROCESS
to false. No code changes.
"""

import asyncio
import logging

log = logging.getLogger("worker")

POLL_INTERVAL_SECONDS = 30


async def run_forever() -> None:
    """Consume queued jobs until cancelled."""
    log.info("worker: started")
    try:
        while True:
            await _drain_queue()
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
    except asyncio.CancelledError:
        log.info("worker: stopping")
        raise


async def _drain_queue() -> None:
    """Claim and run pending jobs.

    Placeholder: the queue table and the ingestion / matching / anchoring jobs
    land here as those features are built.
    """
    return
