from types import SimpleNamespace

from cd_viabilidade.geocoding import GeocoderTimedOut, GeocodingClient


class DummyGeocoder:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def geocode(self, query):
        self.calls.append(query)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_geocode_city_uf_success_and_cache_hit(tmp_path):
    geocoder = DummyGeocoder([SimpleNamespace(latitude=-23.55, longitude=-46.63)])
    cache_file = tmp_path / "geocode_cache.json"
    client = GeocodingClient(cache_path=cache_file, geocoder=geocoder)

    first = client.geocode_city_uf("São Paulo", "SP")
    second = client.geocode_city_uf("São Paulo", "SP")

    assert first.found is True
    assert first.lat == -23.55
    assert first.lon == -46.63
    assert second.source == "cache"
    assert len(geocoder.calls) == 1


def test_geocode_city_uf_retries_on_timeout(tmp_path):
    geocoder = DummyGeocoder(
        [
            GeocoderTimedOut("timeout"),
            GeocoderTimedOut("timeout"),
            SimpleNamespace(latitude=-19.92, longitude=-43.93),
        ]
    )
    sleep_calls = []
    client = GeocodingClient(
        cache_path=tmp_path / "geocode_cache.json",
        geocoder=geocoder,
        max_retries=3,
        backoff_seconds=0.01,
        sleep_fn=sleep_calls.append,
    )

    result = client.geocode_city_uf("Belo Horizonte", "MG")

    assert result.found is True
    assert len(geocoder.calls) == 3
    assert sleep_calls == [0.01, 0.02]


def test_geocode_city_uf_fallback_when_not_found(tmp_path):
    geocoder = DummyGeocoder([None])
    client = GeocodingClient(cache_path=tmp_path / "geocode_cache.csv", geocoder=geocoder)

    result = client.geocode_city_uf("Cidade Inexistente", "ZZ")

    assert result.found is False
    assert result.lat is None
    assert result.lon is None
    assert result.warning is not None
    assert "pipeline seguirá" in result.warning
