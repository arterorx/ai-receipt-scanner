import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings
from app.models.database import init_db

logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="AI Receipt Scanner",
    description="Extract structured data from receipts and invoices using Claude Vision API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)
