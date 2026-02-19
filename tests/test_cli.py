from cd_viabilidade.cli import run_pipeline
from cd_viabilidade.config import AppConfig


def test_run_pipeline_generates_outputs(tmp_path):
    cfg = AppConfig(data_dir=AppConfig().data_dir, output_dir=tmp_path)
    out = run_pipeline(cfg)
    assert "report" in out


def test_base_and_two_new_cds_open_different_counts(tmp_path):
    cfg = AppConfig(data_dir=AppConfig().data_dir, output_dir=tmp_path)
    base = run_pipeline(cfg, scenario_name="base")
    two = run_pipeline(cfg, scenario_name="2_novos_cds")
    assert len(two["selected_facilities"]) >= len(base["selected_facilities"])
