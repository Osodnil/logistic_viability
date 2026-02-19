import pandas as pd

from cd_viabilidade.facility_location import SolutionResult, solve_facility_location


def test_solve_facility_location_returns_deterministic_solution():
    cost_matrix = pd.DataFrame(
        [
            {"facility_id": "F1", "client_id": "C1", "unit_cost": 1},
            {"facility_id": "F2", "client_id": "C1", "unit_cost": 5},
            {"facility_id": "F1", "client_id": "C2", "unit_cost": 5},
            {"facility_id": "F2", "client_id": "C2", "unit_cost": 1},
        ]
    )
    fixed_costs = pd.DataFrame(
        [
            {"facility_id": "F1", "fixed_cost": 1},
            {"facility_id": "F2", "fixed_cost": 10},
        ]
    )

    result = solve_facility_location(cost_matrix, fixed_costs, max_new_facilities=1)

    assert isinstance(result, SolutionResult)
    assert result.open_facilities == ["F1"]
    assert result.allocation == {"C1": "F1", "C2": "F1"}
    assert result.fixed_cost == 1.0
    assert result.variable_cost == 6.0
    assert result.total_cost == 7.0
