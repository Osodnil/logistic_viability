import math

import pandas as pd

from cd_viabilidade.scenarios import (
    DEFAULT_SCENARIOS,
    ScenarioConfig,
    apply_demand_scenario,
    apply_scenario_and_recompute_costs,
    run_scenarios_batch,
)


def _sample_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    candidates = pd.DataFrame(
        [
            {"facility_id": "F1", "lat": -23.5, "lon": -46.6},
            {"facility_id": "F2", "lat": -22.9, "lon": -43.2},
        ]
    )
    demand_points = pd.DataFrame(
        [
            {"client_id": "C1", "lat": -23.6, "lon": -46.7, "demanda": 10},
            {"client_id": "C2", "lat": -22.9, "lon": -43.3, "demanda": 20},
        ]
    )
    return candidates, demand_points


def test_apply_demand_scenario():
    clients = pd.DataFrame([{"client_id": "C1", "demand": 10}])
    out = apply_demand_scenario(clients, {"C1": 1.5})
    assert out.loc[0, "demand_scenario"] == 15


def test_apply_scenario_and_recompute_costs_scales_demand_and_costs():
    candidates, demand_points = _sample_inputs()

    base_matrix = apply_scenario_and_recompute_costs(candidates, demand_points, ScenarioConfig(), tarifa_km=1.0)
    growth_matrix = apply_scenario_and_recompute_costs(
        candidates,
        demand_points,
        ScenarioConfig(crescimento_demanda=0.2),
        tarifa_km=1.0,
    )

    assert math.isclose(growth_matrix["demanda"].sum(), base_matrix["demanda"].sum() * 1.2, rel_tol=1e-9)
    assert math.isclose(growth_matrix["freight_cost"].sum(), base_matrix["freight_cost"].sum() * 1.2, rel_tol=1e-9, abs_tol=0.1)


def test_batch_execution_returns_required_scenarios_and_consistent_aggregates():
    candidates, demand_points = _sample_inputs()

    comparative = run_scenarios_batch(candidates, demand_points, tarifa_km=1.0)

    assert {"base", "1_novo_cd", "2_novos_cds"}.issubset(set(comparative["scenario"]))

    base_row = comparative.loc[comparative["scenario"] == "base"].iloc[0]
    tax_row = comparative.loc[comparative["scenario"] == "tributo_5"].iloc[0]
    salary_row = comparative.loc[comparative["scenario"] == "salario_10"].iloc[0]

    assert tax_row["total_freight_cost"] > base_row["total_freight_cost"]
    assert salary_row["total_freight_cost"] > base_row["total_freight_cost"]

    base_matrix = apply_scenario_and_recompute_costs(candidates, demand_points, DEFAULT_SCENARIOS["base"], tarifa_km=1.0)
    expected_base_cost = round(float(base_matrix["freight_cost"].sum()), 2)
    expected_base_demand = round(float(base_matrix["demanda"].sum()), 4)

    assert base_row["total_freight_cost"] == expected_base_cost
    assert base_row["total_demand"] == expected_base_demand
