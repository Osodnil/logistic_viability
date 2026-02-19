#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
from cd_viabilidade.cli import run_pipeline
from cd_viabilidade.config import AppConfig

result = run_pipeline(AppConfig())
print(f"Relatório gerado em: {result['report']}")
PY
