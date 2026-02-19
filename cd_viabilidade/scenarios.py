"""Geração de cenários de demanda."""

from typing import Dict

import pandas as pd

from .logging_config import configure_logging

logger = configure_logging(logger_name=__name__)


def apply_demand_scenario(clients: pd.DataFrame, multipliers: Dict[str, float]) -> pd.DataFrame:
    """Aplica multiplicadores de demanda por cliente."""
    df = clients.copy()
    df["demand_scenario"] = [
        round(row.demand * multipliers.get(row.client_id, 1.0), 2) for row in df.itertuples()
    ]
    logger.info("Cenário aplicado para %d clientes", len(df))
    return df
