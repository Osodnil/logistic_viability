import pandas as pd

from cd_viabilidade.scenarios import apply_demand_scenario


def test_apply_demand_scenario():
    clients = pd.DataFrame([{"client_id": "C1", "demand": 10}])
    out = apply_demand_scenario(clients, {"C1": 1.5})
    assert out.loc[0, "demand_scenario"] == 15
