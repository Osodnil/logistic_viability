"""Configuração de logging padronizada."""

import logging
from typing import Optional


def configure_logging(level: int = logging.INFO, logger_name: Optional[str] = None) -> logging.Logger:
    """Configura logging padronizado e retorna um logger.

    Args:
        level: Nível de logging.
        logger_name: Nome do logger; se None, usa root.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger(logger_name)
