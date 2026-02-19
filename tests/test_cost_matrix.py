import pandas as pd

from cd_viabilidade.cost_matrix import build_cost_matrix


def test_build_cost_matrix_shape():
    facilities = pd.DataFrame([{"facility_id": "F1", "lat": -23.5, "lon": -46.6}])
    clients = pd.DataFrame([{"client_id": "C1", "lat": -23.6, "lon": -46.7}])
    df = build_cost_matrix(facilities, clients)
    assert len(df) == 1
