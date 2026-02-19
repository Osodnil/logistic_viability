import math

import pandas as pd

from cd_viabilidade.cost_matrix import build_cost_matrix


def test_build_cost_matrix_distance_is_positive():
    candidates = pd.DataFrame([{"facility_id": "F1", "lat": -23.5, "lon": -46.6}])
    demand_points = pd.DataFrame([{"client_id": "C1", "lat": -23.6, "lon": -46.7, "demanda": 10}])

    cost_df = build_cost_matrix(candidates, demand_points, tarifa_km=1.0)

    assert len(cost_df) == 1
    assert cost_df.loc[0, "distance_km"] > 0


def test_build_cost_matrix_costs_are_consistent_with_scenario_params():
    candidates = pd.DataFrame([{"facility_id": "F1", "lat": -23.5, "lon": -46.6}])
    demand_points = pd.DataFrame([{"client_id": "C1", "lat": -23.6, "lon": -46.7, "demanda": 10}])

    long_df, pivot_df = build_cost_matrix(
        candidates,
        demand_points,
        tarifa_km=2.0,
        scenario_params={"tributacao": 0.1, "salario_logistica": 1.2},
        return_pivot=True,
    )

    distance_km = float(long_df.loc[0, "distance_km"])
    expected = round(10 * distance_km * 2.0 * (1 + 0.1) * 1.2, 2)

    assert math.isclose(long_df.loc[0, "freight_cost"], expected, abs_tol=0.05)
    assert math.isclose(pivot_df.loc["C1", "F1"], expected, abs_tol=0.05)


def test_build_cost_matrix_with_missing_coordinates_returns_na_costs():
    candidates = pd.DataFrame([{"facility_id": "F1", "lat": -23.5, "lon": -46.6}])
    demand_points = pd.DataFrame([{"client_id": "C1", "lat": None, "lon": -46.7, "demanda": 10}])

    cost_df = build_cost_matrix(candidates, demand_points)

    assert pd.isna(cost_df.loc[0, "distance_km"])
    assert pd.isna(cost_df.loc[0, "freight_cost"])
