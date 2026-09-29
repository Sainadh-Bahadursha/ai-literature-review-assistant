import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.database.connection import get_db
from src.logger.logging_config import (
    set_request_id,
    setup_logging,
)
from src.utils.request_utils import get_or_create_request_id


setup_logging()

logger = logging.getLogger(__name__)


# ============================================================
# Application Lifespan
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Application starting...")
    logger.info(
        "Application version: %s",
        settings.app_version,
    )
    logger.info(
        "Environment: %s",
        settings.environment,
    )

    yield

    logger.info("Application shutting down...")


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title=settings.app_name,
    description=(
        "Backend API for an AI-powered "
        "literature review assistant"
    ),
    version=settings.app_version,
    lifespan=lifespan,
)


# ============================================================
# Request ID Middleware
# ============================================================

@app.middleware("http")
async def request_id_middleware(
    request: Request,
    call_next,
):

    request_id = get_or_create_request_id(request)

    set_request_id(request_id)

    logger.info(
        "Request started | method=%s | path=%s",
        request.method,
        request.url.path,
    )

    try:

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "Request completed | method=%s | path=%s | status_code=%s",
            request.method,
            request.url.path,
            response.status_code,
        )

        return response

    except Exception:

        logger.exception(
            "Request failed | method=%s | path=%s",
            request.method,
            request.url.path,
        )

        raise


# ============================================================
# Application Health
# ============================================================

@app.get("/health")
def health_check():

    logger.debug(
        "Debug message: health endpoint called"
    )

    logger.info("Health check requested")

    return {
        "status": "healthy",
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


# ============================================================
# Database Health
# ============================================================

@app.get("/health/db")
def database_health_check(
    db: Session = Depends(get_db),
):

    try:

        db.execute(text("SELECT 1"))

        logger.info(
            "Database health check successful"
        )

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception:

        logger.exception(
            "Database health check failed"
        )

        return {
            "status": "unhealthy",
            "database": "connection failed",
        }