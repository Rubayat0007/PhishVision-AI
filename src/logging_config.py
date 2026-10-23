"""Central logging configuration for the PhishVision application."""

import logging
import os

LOGGER_NAME = "phishvision"
DEFAULT_LEVEL = "INFO"
_ENV_VAR = "PHISHVISION_LOG_LEVEL"


def resolve_level(level=None):
    """Resolve an explicit level, the environment, or the default."""
    value = level or os.environ.get(_ENV_VAR, DEFAULT_LEVEL)
    resolved = logging.getLevelName(str(value).strip().upper())

    if not isinstance(resolved, int):
        raise ValueError(f"unsupported log level: {value!r}")

    return resolved


def configure_logging(level=None, handler=None):
    """Configure the package logger once; safe to call repeatedly."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(resolve_level(level))

    if handler is not None:
        logger.addHandler(handler)

    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())

    logger.propagate = False

    return logger


def get_logger(name=None):
    """Return a namespaced child logger."""
    suffix = f".{name}" if name else ""

    return logging.getLogger(f"{LOGGER_NAME}{suffix}")
