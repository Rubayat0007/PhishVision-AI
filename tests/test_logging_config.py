"""Tests for the central logging configuration (torch-free)."""

import logging

import pytest

from src.logging_config import LOGGER_NAME, configure_logging, get_logger, resolve_level


@pytest.fixture(autouse=True)
def clean_logger():
    logger = logging.getLogger(LOGGER_NAME)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
    yield
    for handler in list(logger.handlers):
        logger.removeHandler(handler)


def test_resolve_explicit_level():
    assert resolve_level("debug") == logging.DEBUG


def test_resolve_rejects_unknown_level():
    with pytest.raises(ValueError):
        resolve_level("loud")


def test_environment_variable_is_used(monkeypatch):
    monkeypatch.setenv("PHISHVISION_LOG_LEVEL", "warning")
    assert resolve_level() == logging.WARNING


def test_configure_logging_installs_one_handler():
    logger = configure_logging("ERROR")
    configure_logging("ERROR")

    assert logger.name == LOGGER_NAME
    assert logger.level == logging.ERROR
    assert len(logger.handlers) == 1


def test_child_logger_is_namespaced():
    assert get_logger("predictor").name == "phishvision.predictor"
    assert get_logger().name == LOGGER_NAME
