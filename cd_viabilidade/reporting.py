"""Construção de relatórios textuais de viabilidade."""

from pathlib import Path
from typing import Iterable

from .financials import FinancialSummary
from .logging_config import configure_logging

logger = configure_logging(logger_name=__name__)


def write_markdown_report(output_path: Path, selected_facilities: Iterable[str], summary: FinancialSummary, total_cost: float) -> Path:
    """Gera relatório markdown com principais indicadores."""
    content = "\n".join(
        [
            "# Relatório de Viabilidade Logística",
            "",
            "## Instalações Selecionadas",
            *[f"- {fac}" for fac in selected_facilities],
            "",
            "## Indicadores",
            f"- Custo total otimizado: {total_cost:.2f}",
            f"- Receita: {summary.revenue:.2f}",
            f"- Custo variável: {summary.variable_cost:.2f}",
            f"- Custo fixo: {summary.fixed_cost:.2f}",
            f"- Margem: {summary.margin:.2f}",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    logger.info("Relatório salvo em %s", output_path)
    return output_path
