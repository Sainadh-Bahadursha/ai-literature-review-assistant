import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from src.config.settings import settings
from src.logger.logging_config import set_request_id, setup_logging
from src.utils.request_utils import get_or_create_request_id


# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------

setup_logging()

logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# Application Lifespan
# ------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Application starting...")
    logger.info("Application version: %s", settings.app_version)
    logger.info("Environment: %s", settings.environment)

    yield

    logger.info("Application shutting down...")


# ------------------------------------------------------------
# FastAPI Application
# ------------------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    description="Backend API for an AI-powered literature review assistant",
    version=settings.app_version,
    lifespan=lifespan,
)


# ------------------------------------------------------------
# Request ID Middleware
# ------------------------------------------------------------

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):

    # Get existing request ID or generate a new one
    request_id = get_or_create_request_id(request)

    # Store request ID in the current request context
    set_request_id(request_id)

    logger.info(
        "Request started | method=%s | path=%s",
        request.method,
        request.url.path,
    )

    try:

        response = await call_next(request)

        # Return request ID to the client
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


# ------------------------------------------------------------
# Health Check
# ------------------------------------------------------------

@app.get("/health")
def health_check():

    logger.debug("Debug message: health endpoint called")

    logger.info("Health check requested")

    return {
        "status": "healthy",
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }