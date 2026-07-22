"""Standalone worker entrypoint: `python -m app.worker`.

Not used in the current deployment (the worker runs in-process with the API).
Kept so promoting the worker to its own Fly process group is a config change
rather than a rewrite.
"""

import asyncio
import logging

from app.worker.runner import run_forever

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    asyncio.run(run_forever())
