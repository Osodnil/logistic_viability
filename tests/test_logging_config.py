import logging

from cd_viabilidade.logging_config import configure_logging


def test_configure_logging_returns_logger():
    logger = configure_logging(logging.INFO, "x")
    assert logger.name == "x"
