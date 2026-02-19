from cd_viabilidade.api import healthcheck


def test_healthcheck():
    assert healthcheck()["status"] == "ok"
