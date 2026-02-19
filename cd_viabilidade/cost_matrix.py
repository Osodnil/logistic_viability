"""Cálculo de matriz de custos logísticos."""

from __future__ import annotations

from typing import Any, Dict, Tuple

import pandas as pd
from geopy.distance import distance

from .logging_config import configure_logging

logger = configure_logging(logger_name=__name__)


DEFAULT_SCENARIO_PARAMS: Dict[str, float] = {
    "tributacao": 0.0,
    "salario_logistica": 1.0,
}


def _safe_distance_km(
    demand_lat: Any,
    demand_lon: Any,
    candidate_lat: Any,
    candidate_lon: Any,
) -> float | None:
    """Calcula distância em km entre dois pontos, retornando ``None`` se houver ausência de coordenadas."""
    if pd.isna(demand_lat) or pd.isna(demand_lon) or pd.isna(candidate_lat) or pd.isna(candidate_lon):
        return None
    return float(distance((demand_lat, demand_lon), (candidate_lat, candidate_lon)).km)


def _compute_freight_cost(
    demand: float,
    distance_km: float,
    tarifa_km: float,
    tributacao: float,
    salario_logistica: float,
) -> float:
    """Calcula custo de frete com parâmetros de cenário."""
    base_cost = demand * distance_km * tarifa_km
    return float(base_cost * (1 + tributacao) * salario_logistica)


def build_cost_matrix(
    candidates: pd.DataFrame,
    demand_points: pd.DataFrame,
    tarifa_km: float = 1.2,
    scenario_params: Dict[str, float] | None = None,
    return_pivot: bool = False,
) -> pd.DataFrame | Tuple[pd.DataFrame, pd.DataFrame]:
    """Gera matriz de custos demanda-candidato.

    Espera as colunas:
    - ``candidates``: ``facility_id``, ``lat``, ``lon``
    - ``demand_points``: ``client_id``, ``lat``, ``lon`` e opcionalmente ``demanda``

    A fórmula padrão é: ``custo = demanda * distancia_km * tarifa_km``
    e pode ser ajustada via ``scenario_params`` com:
    - ``tributacao``: percentual adicional (ex: 0.15 para 15%)
    - ``salario_logistica``: fator multiplicador de custo logístico
    """
    params = {**DEFAULT_SCENARIO_PARAMS, **(scenario_params or {})}
    tributacao = float(params["tributacao"])
    salario_logistica = float(params["salario_logistica"])

    rows: list[dict[str, Any]] = []
    for _, candidate in candidates.iterrows():
        for _, demand_point in demand_points.iterrows():
            demand_value = float(demand_point.get("demanda", 1.0))
            dist_km = _safe_distance_km(
                demand_point["lat"],
                demand_point["lon"],
                candidate["lat"],
                candidate["lon"],
            )

            if dist_km is None:
                freight_cost = pd.NA
                distance_km = pd.NA
            else:
                distance_km = round(dist_km, 3)
                freight_cost = round(
                    _compute_freight_cost(
                        demand=demand_value,
                        distance_km=dist_km,
                        tarifa_km=tarifa_km,
                        tributacao=tributacao,
                        salario_logistica=salario_logistica,
                    ),
                    2,
                )

            rows.append(
                {
                    "facility_id": candidate["facility_id"],
                    "client_id": demand_point["client_id"],
                    "demanda": demand_value,
                    "distance_km": distance_km,
                    "freight_cost": freight_cost,
                    "tributacao": tributacao,
                    "salario_logistica": salario_logistica,
                }
            )

    long_df = pd.DataFrame(rows)
    logger.info("Matriz de custo criada com %d linhas", len(long_df))

    if not return_pivot:
        return long_df

    pivot_df = long_df.pivot(index="client_id", columns="facility_id", values="freight_cost")
    return long_df, pivot_df
