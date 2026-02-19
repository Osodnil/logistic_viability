from cd_viabilidade.config import AppConfig


def test_config_defaults():
    cfg = AppConfig()
    assert cfg.default_facility_limit == 2
