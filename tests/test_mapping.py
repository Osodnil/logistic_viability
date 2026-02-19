import pandas as pd

from cd_viabilidade.mapping import build_map


def test_build_map(tmp_path):
    facilities = pd.DataFrame([{"facility_id": "F1", "lat": -23.5, "lon": -46.6}])
    clients = pd.DataFrame([{"client_id": "C1", "lat": -23.6, "lon": -46.7}])
    output = build_map(facilities, clients, tmp_path / "map.html")
    assert output.exists()
