from fastapi import FastAPI

from app.api import health

app = FastAPI(
    title="la-vie-en-rose",
    description="Walking every street of Paris — API",
    version="0.1.0",
)

app.include_router(health.router)
