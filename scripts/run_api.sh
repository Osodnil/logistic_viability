#!/usr/bin/env bash
set -euo pipefail
uvicorn cd_viabilidade.api:app --host 0.0.0.0 --port 8000
