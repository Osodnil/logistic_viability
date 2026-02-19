import pandas as pd

from cd_viabilidade.auto_costs import estimate_fixed_costs


def test_estimate_fixed_costs_generates_expected_columns():
    facilities = pd.DataFrame(
        {
            "facility_id": ["F1", "F2"],
            "uf": ["SP", "MG"],
            "ocupacao": [0.8, 0.6],
            "capacidade_m2": [5000, 3500],
        }
    )
    regional = pd.DataFrame(
        {
            "uf": ["SP", "MG"],
            "labor_cost_index": [1.1, 0.9],
            "real_estate_cost_m2": [60, 40],
            "tax_factor": [0.1, 0.08],
            "transport_factor": [1.05, 0.95],
        }
    )

    out = estimate_fixed_costs(facilities, regional)

    assert {"facility_id", "fixed_cost", "labor_cost", "inbound_cost"}.issubset(out.columns)
    assert (out["fixed_cost"] > 0).all()
