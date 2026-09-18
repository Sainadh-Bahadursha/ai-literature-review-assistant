import logging
import os
from contextvars import ContextVar
from datetime import datetime

from logtail import LogtailHandler

from src.config.settings import settings


# ============================================================
# Request ID
# ============================================================

request_id_context: ContextVar[str] = ContextVar(
    "request_id",
    default="-",
)


def set_request_id(request_id: str):
    """
    Store the request ID for the current request context.
    """
    request_id_context.set(request_id)


def get_request_id() -> str:
    """
    Return the request ID for the current request context.
    """
    return request_id_context.get()


# ============================================================
# Logging Filter
# ============================================================

class RequestIDFilter(logging.Filter):
    """
    Add request_id to every log record.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


# ============================================================
# Log Format
# ============================================================

LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(filename)s:%(lineno)d | "
    "%(funcName)s() | "
    "request_id=%(request_id)s | "
    "%(message)s"
)


# ============================================================
# Log Level
# ============================================================

def get_log_level() -> int:
    """
    Convert configured log level string into
    the corresponding Python logging level.
    """

    level = settings.log_level.upper()

    return getattr(logging, level, logging.DEBUG)


# ============================================================
# Logging Setup
# ============================================================

def setup_logging():
    """
    Configure application logging based on environment.

    Development:
        Console -> DEBUG+
        File    -> DEBUG+
        Better Stack -> Disabled

    Testing:
        Console -> DEBUG+
        File    -> DEBUG+
        Better Stack -> Disabled

    Production:
        Console -> INFO+
        File    -> Disabled
        Better Stack -> INFO+
    """

    root_logger = logging.getLogger()

    # --------------------------------------------------------
    # Remove existing handlers
    # --------------------------------------------------------

    root_logger.handlers.clear()

    # --------------------------------------------------------
    # Environment
    # --------------------------------------------------------

    environment = settings.environment.lower()

    # --------------------------------------------------------
    # Better Stack safety check
    # --------------------------------------------------------

    if environment != "production" and settings.betterstack_enabled:
        raise ValueError(
            "Better Stack can only be enabled in production."
        )

    # --------------------------------------------------------
    # Formatter and Filter
    # --------------------------------------------------------

    formatter = logging.Formatter(LOG_FORMAT)

    request_id_filter = RequestIDFilter()

    # ========================================================
    # DEVELOPMENT / TESTING
    # ========================================================

    if environment in ("development", "testing"):

        log_level = get_log_level()

        root_logger.setLevel(log_level)

        # ----------------------------------------------------
        # Console Handler
        # ----------------------------------------------------

        console_handler = logging.StreamHandler()

        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(request_id_filter)

        root_logger.addHandler(console_handler)

        # ----------------------------------------------------
        # File Handler
        # ----------------------------------------------------

        if settings.log_file_enabled:

            os.makedirs("logs", exist_ok=True)

            timestamp = datetime.now().strftime(
                "%Y-%m-%d_%H-%M-%S"
            )

            log_file = f"logs/app_{timestamp}.log"

            file_handler = logging.FileHandler(
                log_file,
                encoding="utf-8",
            )

            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            file_handler.addFilter(request_id_filter)

            root_logger.addHandler(file_handler)

    # ========================================================
    # PRODUCTION
    # ========================================================

    elif environment == "production":

        # ----------------------------------------------------
        # Production MUST use INFO+
        # ----------------------------------------------------

        root_logger.setLevel(logging.INFO)

        # ----------------------------------------------------
        # Console Handler
        # ----------------------------------------------------

        console_handler = logging.StreamHandler()

        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(request_id_filter)

        root_logger.addHandler(console_handler)

        # ----------------------------------------------------
        # Better Stack
        # ----------------------------------------------------

        if settings.betterstack_enabled:

            if not settings.betterstack_source_token:
                raise ValueError(
                    "BETTERSTACK_SOURCE_TOKEN is required "
                    "when Better Stack is enabled."
                )

            if not settings.betterstack_ingesting_host:
                raise ValueError(
                    "BETTERSTACK_INGESTING_HOST is required "
                    "when Better Stack is enabled."
                )

            betterstack_handler = LogtailHandler(
                source_token=settings.betterstack_source_token,
                host=settings.betterstack_ingesting_host,
            )

            # Better Stack receives INFO+
            betterstack_handler.setLevel(logging.INFO)
            betterstack_handler.setFormatter(formatter)
            betterstack_handler.addFilter(request_id_filter)

            root_logger.addHandler(
                betterstack_handler
            )

    # ========================================================
    # INVALID ENVIRONMENT
    # ========================================================

    else:

        raise ValueError(
            f"Unsupported environment: {settings.environment}"
        )

    # ========================================================
    # Initialization Log
    # ========================================================

    logger = logging.getLogger(__name__)

    logger.info(
        "Logging initialized | environment=%s",
        environment,
    )