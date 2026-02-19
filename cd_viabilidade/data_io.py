"""Funções de leitura e escrita de datasets."""

from pathlib import Path
from typing import Iterable

import pandas as pd

from .logging_config import configure_logging

logger = configure_logging(logger_name=__name__)


def load_csv(path: Path) -> pd.DataFrame:
    """Carrega um CSV em DataFrame."""
    logger.info("Carregando CSV: %s", path)
    return pd.read_csv(path)


def save_csv(df: pd.DataFrame, path: Path) -> None:
    """Salva um DataFrame em CSV."""
    logger.info("Salvando CSV: %s", path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def require_columns(df: pd.DataFrame, required: Iterable[str]) -> None:
    """Valida se todas as colunas obrigatórias existem."""
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"Colunas ausentes: {missing}")
