import pandas as pd

from cd_viabilidade.financials import compute_financials


def test_compute_financials_margin():
    assignments = pd.DataFrame([{"facility_id": "F1", "client_id": "C1"}])
    cost_matrix = pd.DataFrame([{"facility_id": "F1", "client_id": "C1", "unit_cost": 40}])
    summary = compute_financials(assignments, cost_matrix, unit_revenue=100, fixed_cost=20)
    assert summary.margin == 40
