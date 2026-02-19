"""API FastAPI para execução de cenários de viabilidade."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from .cli import execute_scenario, generate_report
from .config import AppConfig
from .logging_config import configure_logging
from .scenarios import ScenarioConfig

logger = configure_logging(logger_name=__name__)
app = FastAPI(title="API de Viabilidade Logística")


class OptimizeRequest(BaseModel):
    scenario_name: str = "custom"
    crescimento_demanda: float = 0.0
    fator_tributario: float = 0.0
    fator_salarial: float = 1.0
    limite_novos_cds: int | None = None


@app.get("/health")
def healthcheck() -> dict:
    """Endpoint simples de saúde."""
    return {"status": "ok"}


@app.post("/optimize")
def optimize(payload: OptimizeRequest) -> dict:
    """Executa otimização com parâmetros de cenário enviados no payload."""
    logger.info("Recebida requisição /optimize para cenário %s", payload.scenario_name)
    scenario = ScenarioConfig(
        crescimento_demanda=payload.crescimento_demanda,
        fator_tributario=payload.fator_tributario,
        fator_salarial=payload.fator_salarial,
        limite_novos_cds=payload.limite_novos_cds,
    )
    return execute_scenario(AppConfig(), scenario_name=payload.scenario_name, scenario=scenario)


@app.get("/report")
def report() -> dict:
    """Gera relatório executivo e retorna caminho/preview."""
    report_path = generate_report(AppConfig())
    preview = Path(report_path).read_text(encoding="utf-8")[:500]
    return {"report_path": str(report_path), "preview": preview}
