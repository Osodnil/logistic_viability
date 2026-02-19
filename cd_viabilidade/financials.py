"""Cálculos financeiros para avaliação de viabilidade."""

from dataclasses import dataclass

import pandas as pd

from .logging_config import configure_logging

logger = configure_logging(logger_name=__name__)


@dataclass(frozen=True)
class FinancialSummary:
    """Resumo financeiro consolidado."""

    revenue: float
    variable_cost: float
    fixed_cost: float
    margin: float


def compute_financials(assignments: pd.DataFrame, cost_matrix: pd.DataFrame, unit_revenue: float, fixed_cost: float) -> FinancialSummary:
    """Calcula receita, custos e margem."""
    merged = assignments.merge(cost_matrix[["facility_id", "client_id", "unit_cost"]], on=["facility_id", "client_id"])
    variable_cost = float(merged["unit_cost"].sum())
    revenue = float(len(merged) * unit_revenue)
    margin = revenue - variable_cost - fixed_cost
    summary = FinancialSummary(revenue=revenue, variable_cost=variable_cost, fixed_cost=fixed_cost, margin=margin)
    logger.info("Resumo financeiro calculado: %s", summary)
    return summary
