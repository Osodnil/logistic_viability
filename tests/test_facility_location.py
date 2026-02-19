import pandas as pd

from cd_viabilidade.facility_location import solve_facility_location


def test_solve_facility_location_runs():
    cost = pd.DataFrame([
        {"facility_id": "F1", "client_id": "C1", "unit_cost": 10},
        {"facility_id": "F2", "client_id": "C1", "unit_cost": 20},
    ])
    fixed = pd.DataFrame([
        {"facility_id": "F1", "fixed_cost": 5},
        {"facility_id": "F2", "fixed_cost": 1},
    ])
    selected, assignments, total = solve_facility_location(cost, fixed, 1)
    assert len(selected) == 1
    assert len(assignments) == 1
    assert total > 0
