import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config.settings import settings
from src.logger.logging_config import setup_logging


setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting...")
    logger.info("Application version: %s", settings.app_version)

    yield

    logger.info("Application shutting down...")


app = FastAPI(
    title=settings.app_name,
    description="Backend API for an AI-powered literature review assistant",
    version=settings.app_version,
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    logger.info("Health check requested")

    return {
        "status": "healthy",
        "application": settings.app_name,
        "version": settings.app_version,
    }