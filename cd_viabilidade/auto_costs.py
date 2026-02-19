"""Estimativa automática de custos de CD com base em proxies regionais."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .logging_config import configure_logging

logger = configure_logging(logger_name=__name__)


@dataclass(frozen=True)
class CostEstimationConfig:
    """Parâmetros globais para estimativa automática de custos."""

    capacidade_padrao_m2: float = 4_000.0
    custo_utilidades_pct: float = 0.12
    custo_overhead_pct: float = 0.08
    custo_inbound_base: float = 80_000.0


def _safe_series(df: pd.DataFrame, column: str, default: float) -> pd.Series:
    if column in df.columns:
        return pd.to_numeric(df[column], errors="coerce").fillna(default)
    return pd.Series(default, index=df.index, dtype=float)


def estimate_fixed_costs(
    facilities: pd.DataFrame,
    regional_costs: pd.DataFrame,
    *,
    config: CostEstimationConfig | None = None,
) -> pd.DataFrame:
    """Estima custo fixo operacional por instalação com base em custos regionais.

    Espera em ``regional_costs`` colunas:
    - ``uf``
    - ``labor_cost_index``
    - ``real_estate_cost_m2``
    - ``tax_factor``
    - ``transport_factor``
    """
    cfg = config or CostEstimationConfig()

    required = {"uf", "labor_cost_index", "real_estate_cost_m2", "tax_factor", "transport_factor"}
    missing = sorted(required - set(regional_costs.columns))
    if missing:
        raise ValueError(f"regional_costs.csv sem colunas obrigatórias: {missing}")

    if "facility_id" not in facilities.columns:
        raise ValueError("facilities.csv deve conter coluna 'facility_id'")
    if "uf" not in facilities.columns:
        raise ValueError("facilities.csv deve conter coluna 'uf' para estimação automática")

    merged = facilities.merge(regional_costs, on="uf", how="left", validate="many_to_one")
    if merged[["labor_cost_index", "real_estate_cost_m2", "tax_factor", "transport_factor"]].isna().any().any():
        raise ValueError("Há facilities sem parâmetros regionais. Verifique correspondência de UF em regional_costs.csv")

    capacidade_m2 = _safe_series(merged, "capacidade_m2", cfg.capacidade_padrao_m2)
    ocupacao = _safe_series(merged, "ocupacao", 0.75).clip(lower=0.1, upper=1.0)

    labor_cost = merged["labor_cost_index"].astype(float) * ocupacao * 250_000.0
    real_estate_cost = merged["real_estate_cost_m2"].astype(float) * capacidade_m2
    utilities = (labor_cost + real_estate_cost) * cfg.custo_utilidades_pct
    overhead = (labor_cost + real_estate_cost) * cfg.custo_overhead_pct
    inbound_cost = cfg.custo_inbound_base * merged["transport_factor"].astype(float)

    operational = labor_cost + real_estate_cost + utilities + overhead + inbound_cost
    total_fixed = operational * (1.0 + merged["tax_factor"].astype(float))

    out = pd.DataFrame(
        {
            "facility_id": merged["facility_id"].astype(str),
            "labor_cost": labor_cost.round(2),
            "real_estate_cost": real_estate_cost.round(2),
            "utilities_cost": utilities.round(2),
            "overhead_cost": overhead.round(2),
            "inbound_cost": inbound_cost.round(2),
            "tax_factor": merged["tax_factor"].astype(float).round(4),
            "fixed_cost": total_fixed.round(2),
        }
    )
    logger.info("Custos fixos estimados automaticamente para %d facilities", len(out))
    return out
