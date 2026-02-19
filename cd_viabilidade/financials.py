"""Cálculos financeiros para avaliação de viabilidade."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from .logging_config import configure_logging

logger = configure_logging(logger_name=__name__)


@dataclass(frozen=True)
class FinancialSummary:
    """Resumo financeiro consolidado de operação."""

    revenue: float
    variable_cost: float
    fixed_cost: float
    margin: float


@dataclass(frozen=True)
class FinancialIndicators:
    """Indicadores financeiros para decisão de investimento."""

    npv: float
    payback_simple: float | None
    payback_discounted: float | None
    roi: float


def compute_financials(assignments: pd.DataFrame, cost_matrix: pd.DataFrame, unit_revenue: float, fixed_cost: float) -> FinancialSummary:
    """Calcula receita, custos e margem."""
    cost_column = "unit_cost" if "unit_cost" in cost_matrix.columns else "freight_cost"
    merged = assignments.merge(cost_matrix[["facility_id", "client_id", cost_column]], on=["facility_id", "client_id"])
    variable_cost = float(merged[cost_column].sum())
    revenue = float(len(merged) * unit_revenue)
    margin = revenue - variable_cost - fixed_cost
    summary = FinancialSummary(revenue=revenue, variable_cost=variable_cost, fixed_cost=fixed_cost, margin=margin)
    logger.info("Resumo financeiro calculado: %s", summary)
    return summary


def _normalize_cashflows(annual_savings: float | Iterable[float], horizon_years: int) -> list[float]:
    if isinstance(annual_savings, (int, float)):
        return [float(annual_savings)] * horizon_years

    cashflows = [float(value) for value in annual_savings]
    if len(cashflows) != horizon_years:
        raise ValueError("Quantidade de fluxos anuais deve ser igual ao horizonte de anos.")
    return cashflows


def calculate_npv(
    initial_investment: float,
    annual_savings: float | Iterable[float],
    horizon_years: int,
    discount_rate: float,
) -> float:
    """Calcula VPL com fluxo de economia anual versus baseline."""
    cashflows = _normalize_cashflows(annual_savings, horizon_years)
    discounted_sum = sum(cf / ((1 + discount_rate) ** year) for year, cf in enumerate(cashflows, start=1))
    return discounted_sum - float(initial_investment)


def calculate_payback_simple(initial_investment: float, annual_savings: float | Iterable[float], horizon_years: int) -> float | None:
    """Calcula payback simples (anos), retornando None se não recuperar no horizonte."""
    cashflows = _normalize_cashflows(annual_savings, horizon_years)
    cumulative = 0.0
    for year, flow in enumerate(cashflows, start=1):
        if flow <= 0:
            cumulative += flow
            continue
        previous = cumulative
        cumulative += flow
        if cumulative >= initial_investment:
            residual = initial_investment - previous
            return (year - 1) + (residual / flow)
    return None


def calculate_payback_discounted(
    initial_investment: float,
    annual_savings: float | Iterable[float],
    horizon_years: int,
    discount_rate: float,
) -> float | None:
    """Calcula payback descontado (anos), retornando None se não recuperar no horizonte."""
    cashflows = _normalize_cashflows(annual_savings, horizon_years)
    cumulative = 0.0
    for year, flow in enumerate(cashflows, start=1):
        discounted = flow / ((1 + discount_rate) ** year)
        if discounted <= 0:
            cumulative += discounted
            continue
        previous = cumulative
        cumulative += discounted
        if cumulative >= initial_investment:
            residual = initial_investment - previous
            return (year - 1) + (residual / discounted)
    return None


def calculate_roi(initial_investment: float, annual_savings: float | Iterable[float], horizon_years: int) -> float:
    """Calcula ROI acumulado no horizonte usando economia total versus investimento."""
    cashflows = _normalize_cashflows(annual_savings, horizon_years)
    total_savings = sum(cashflows)
    if initial_investment == 0:
        raise ValueError("Investimento inicial não pode ser zero para cálculo de ROI.")
    return (total_savings - initial_investment) / initial_investment


def calculate_financial_indicators(
    initial_investment: float,
    annual_savings: float | Iterable[float],
    horizon_years: int,
    discount_rate: float,
) -> FinancialIndicators:
    """Consolida VPL, paybacks e ROI para um cenário de abertura de CDs."""
    indicators = FinancialIndicators(
        npv=calculate_npv(initial_investment, annual_savings, horizon_years, discount_rate),
        payback_simple=calculate_payback_simple(initial_investment, annual_savings, horizon_years),
        payback_discounted=calculate_payback_discounted(initial_investment, annual_savings, horizon_years, discount_rate),
        roi=calculate_roi(initial_investment, annual_savings, horizon_years),
    )
    logger.info("Indicadores financeiros calculados: %s", indicators)
    return indicators
