"""Geração e execução de cenários de viabilidade logística."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping

import pandas as pd

from .cost_matrix import build_cost_matrix
from .logging_config import configure_logging

logger = configure_logging(logger_name=__name__)


@dataclass(frozen=True)
class ScenarioConfig:
    """Configuração de cenário para simulações de viabilidade."""

    crescimento_demanda: float = 0.0
    fator_tributario: float = 0.0
    fator_salarial: float = 1.0
    limite_novos_cds: int | None = None


DEFAULT_SCENARIOS: Dict[str, ScenarioConfig] = {
    "base": ScenarioConfig(),
    "1_novo_cd": ScenarioConfig(limite_novos_cds=1),
    "2_novos_cds": ScenarioConfig(limite_novos_cds=2),
    "crescimento_10": ScenarioConfig(crescimento_demanda=0.10),
    "tributo_5": ScenarioConfig(fator_tributario=0.05),
    "salario_10": ScenarioConfig(fator_salarial=1.10),
}


def _resolve_demand_column(df: pd.DataFrame) -> str:
    if "demanda" in df.columns:
        return "demanda"
    if "demand" in df.columns:
        return "demand"
    raise ValueError("DataFrame de demanda deve conter coluna 'demanda' ou 'demand'.")


def apply_demand_scenario(clients: pd.DataFrame, multipliers: Dict[str, float]) -> pd.DataFrame:
    """Aplica multiplicadores de demanda por cliente."""
    df = clients.copy()
    demand_col = _resolve_demand_column(df)
    df["demand_scenario"] = [
        round(getattr(row, demand_col) * multipliers.get(row.client_id, 1.0), 2)
        for row in df.itertuples()
    ]
    logger.info("Cenário aplicado para %d clientes", len(df))
    return df


def apply_scenario_and_recompute_costs(
    candidates: pd.DataFrame,
    demand_points: pd.DataFrame,
    scenario: ScenarioConfig,
    tarifa_km: float = 1.2,
) -> pd.DataFrame:
    """Aplica cenário nos dados de demanda e recompõe a matriz de custos."""
    demand_col = _resolve_demand_column(demand_points)

    scenario_demand = demand_points.copy()
    scenario_demand["demanda"] = (
        scenario_demand[demand_col].astype(float) * (1 + scenario.crescimento_demanda)
    )

    cost_matrix = build_cost_matrix(
        candidates,
        scenario_demand,
        tarifa_km=tarifa_km,
        scenario_params={
            "tributacao": scenario.fator_tributario,
            "salario_logistica": scenario.fator_salarial,
        },
    )
    return cost_matrix


def run_scenarios_batch(
    candidates: pd.DataFrame,
    demand_points: pd.DataFrame,
    scenarios: Mapping[str, ScenarioConfig] | None = None,
    tarifa_km: float = 1.2,
) -> pd.DataFrame:
    """Executa múltiplos cenários e retorna tabela comparativa consolidada."""
    selected = dict(scenarios or DEFAULT_SCENARIOS)

    comparative_rows: list[dict[str, float | int | str | None]] = []
    for scenario_name, scenario in selected.items():
        cost_matrix = apply_scenario_and_recompute_costs(
            candidates=candidates,
            demand_points=demand_points,
            scenario=scenario,
            tarifa_km=tarifa_km,
        )

        total_freight_cost = float(cost_matrix["freight_cost"].sum())
        total_demand = float(cost_matrix["demanda"].sum())
        comparative_rows.append(
            {
                "scenario": scenario_name,
                "crescimento_demanda": scenario.crescimento_demanda,
                "fator_tributario": scenario.fator_tributario,
                "fator_salarial": scenario.fator_salarial,
                "limite_novos_cds": scenario.limite_novos_cds,
                "total_demand": round(total_demand, 4),
                "total_freight_cost": round(total_freight_cost, 2),
                "avg_cost_per_unit": round(total_freight_cost / total_demand, 6) if total_demand else 0.0,
            }
        )

    comparative_df = pd.DataFrame(comparative_rows).sort_values("scenario").reset_index(drop=True)
    logger.info("Execução em lote concluída para %d cenários", len(comparative_df))
    return comparative_df
