import pytest
import pandas as pd

from cd_viabilidade.financials import (
    calculate_financial_indicators,
    calculate_npv,
    calculate_payback_discounted,
    calculate_payback_simple,
    calculate_roi,
    compute_financials,
)


def test_compute_financials_margin():
    assignments = pd.DataFrame([{"facility_id": "F1", "client_id": "C1"}])
    cost_matrix = pd.DataFrame([{"facility_id": "F1", "client_id": "C1", "unit_cost": 40}])
    summary = compute_financials(assignments, cost_matrix, unit_revenue=100, fixed_cost=20)
    assert summary.margin == 40


def test_calculate_npv_constant_cashflow():
    npv = calculate_npv(initial_investment=1000, annual_savings=400, horizon_years=3, discount_rate=0.10)
    assert npv == pytest.approx(-5.26, abs=0.02)


def test_payback_simple_and_discounted():
    simple = calculate_payback_simple(initial_investment=1000, annual_savings=400, horizon_years=5)
    discounted = calculate_payback_discounted(
        initial_investment=1000,
        annual_savings=400,
        horizon_years=5,
        discount_rate=0.10,
    )
    assert simple == pytest.approx(2.5)
    assert discounted == pytest.approx(3.02, abs=0.02)


def test_calculate_roi():
    roi = calculate_roi(initial_investment=1000, annual_savings=400, horizon_years=3)
    assert roi == pytest.approx(0.2)


def test_calculate_financial_indicators_with_list_cashflow():
    indicators = calculate_financial_indicators(
        initial_investment=1000,
        annual_savings=[300, 350, 500],
        horizon_years=3,
        discount_rate=0.10,
    )
    assert indicators.npv == pytest.approx(-62.36, abs=0.02)
    assert indicators.payback_simple == pytest.approx(2.7, abs=0.01)
    assert indicators.payback_discounted is None
    assert indicators.roi == pytest.approx(0.15)
