"""Structured logging configuration."""

import logging
import sys
from logging.config import dictConfig

from config import settings

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
REQUEST_LOG_FORMAT = "%(method)s %(path)s %(status_code)s %(duration_ms).1fms"
SECRET_KEYS = ("password", "encrypted_key", "authorization", "token")


def configure_logging() -> None:
    """Install the process wide logging configuration.

    Console JSON-ish lines are used everywhere; Sentry captures anything at
    ``ERROR`` or above through the integrations registered in ``server.py``.
    """
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": LOG_FORMAT,
                    "datefmt": DATE_FORMAT,
                },
                "access": {
                    "format": REQUEST_LOG_FORMAT,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": sys.stdout,
                    "formatter": "default",
                },
            },
            "root": {
                "handlers": ["console"],
                "level": settings.LOG_LEVEL,
            },
            "loggers": {
                "uvicorn.access": {"handlers": [], "propagate": True},
                "sqlalchemy.engine": {
                    "level": "INFO" if settings.DATABASE_ECHO else "WARNING",
                },
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Return a module scoped logger.

    :param name: Usually ``__name__`` of the calling module.
    :return: Configured logger instance.
    """
    return logging.getLogger(name)


def redact(data: dict[str, object]) -> dict[str, object]:
    """Return a copy of ``data`` with secret fields masked.

    :param data: Payload about to be logged.
    :return: Log safe copy of the payload.
    """
    return {
        key: "***" if any(secret in key.lower() for secret in SECRET_KEYS) else value
        for key, value in data.items()
    }
