from cd_viabilidade.geocoding import deterministic_geocode


def test_deterministic_geocode_reproducible():
    c1 = deterministic_geocode("Rua A")
    c2 = deterministic_geocode("Rua A")
    assert c1 == c2
