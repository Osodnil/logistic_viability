from cd_viabilidade.cli import run_pipeline
from cd_viabilidade.config import AppConfig


def test_run_pipeline_generates_outputs(tmp_path):
    cfg = AppConfig(data_dir=AppConfig().data_dir, output_dir=tmp_path)
    out = run_pipeline(cfg)
    assert "report" in out
