"""API FastAPI para execução de cenários de viabilidade."""

from fastapi import FastAPI

from .cli import run_pipeline
from .config import AppConfig
from .logging_config import configure_logging

logger = configure_logging(logger_name=__name__)
app = FastAPI(title="API de Viabilidade Logística")


@app.get("/health")
def healthcheck() -> dict:
    """Endpoint simples de saúde."""
    return {"status": "ok"}


@app.post("/run")
def run() -> dict:
    """Executa pipeline completo com configuração padrão."""
    logger.info("Recebida requisição de execução")
    return run_pipeline(AppConfig())
