"""Cálculo de matriz de custos logísticos."""

from typing import List

import pandas as pd
from geopy.distance import geodesic

from .logging_config import configure_logging

logger = configure_logging(logger_name=__name__)


def build_cost_matrix(facilities: pd.DataFrame, clients: pd.DataFrame, cost_per_km: float = 1.2) -> pd.DataFrame:
    """Calcula matriz de custo por cliente e instalação."""
    rows: List[dict] = []
    for _, fac in facilities.iterrows():
        for _, cli in clients.iterrows():
            km = geodesic((fac["lat"], fac["lon"]), (cli["lat"], cli["lon"])).km
            rows.append(
                {
                    "facility_id": fac["facility_id"],
                    "client_id": cli["client_id"],
                    "distance_km": round(km, 3),
                    "unit_cost": round(km * cost_per_km, 2),
                }
            )
    matrix = pd.DataFrame(rows)
    logger.info("Matriz de custo criada com %d linhas", len(matrix))
    return matrix
