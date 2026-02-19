"""Construção de relatórios textuais de viabilidade."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .financials import FinancialIndicators, FinancialSummary
from .logging_config import configure_logging

logger = configure_logging(logger_name=__name__)


def write_markdown_report(output_path: Path, selected_facilities: Iterable[str], summary: FinancialSummary, total_cost: float) -> Path:
    """Gera relatório markdown com principais indicadores operacionais."""
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


def _format_payback(payback: float | None) -> str:
    return "não recupera no horizonte" if payback is None else f"{payback:.2f} anos"


def generate_executive_report(
    scenario_costs: dict[str, float],
    scenario_indicators: dict[str, FinancialIndicators],
    output_dir: Path = Path("outputs"),
) -> Path:
    """Gera relatório executivo com recomendação acionável baseada no cenário base."""
    if "base" not in scenario_costs or "base" not in scenario_indicators:
        raise ValueError("Cenário 'base' é obrigatório no relatório executivo")

    shared_scenarios = sorted(set(scenario_costs).intersection(scenario_indicators))
    if not shared_scenarios:
        raise ValueError("Nenhum cenário comum entre custos e indicadores")

    base_cost = scenario_costs["base"]
    base_ind = scenario_indicators["base"]

    candidate_names = [name for name in shared_scenarios if name != "base"]
    best_name = "base"
    best_npv = base_ind.npv
    for name in candidate_names:
        if scenario_indicators[name].npv > best_npv:
            best_npv = scenario_indicators[name].npv
            best_name = name

    if best_name == "base":
        recommendation = "Manter cenário base"
    else:
        recommendation = f"Avançar com cenário {best_name}"

    summary_lines = [f"- {name}: custo anual {scenario_costs[name]:.2f}" for name in shared_scenarios]
    comparative_lines = [
        f"- {name} vs base: redução anual estimada {base_cost - scenario_costs[name]:.2f}"
        for name in candidate_names
    ]
    indicator_lines = [
        (
            f"- {name}: VPL={scenario_indicators[name].npv:.2f}, "
            f"Payback={_format_payback(scenario_indicators[name].payback_simple)}, "
            f"Payback descontado={_format_payback(scenario_indicators[name].payback_discounted)}, "
            f"ROI={scenario_indicators[name].roi:.2%}"
        )
        for name in shared_scenarios
    ]

    content = "\n".join(
        [
            "# Relatório Executivo de Viabilidade",
            "",
            "## Resumo dos cenários",
            *summary_lines,
            "",
            "## Custos comparativos",
            *comparative_lines,
            "",
            "## Indicadores financeiros",
            *indicator_lines,
            "",
            "## Recomendação acionável",
            f"- {recommendation}, priorizando critérios financeiros de VPL e recuperação de investimento.",
        ]
    )

    output_path = output_dir / "relatorio_executivo.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    logger.info("Relatório executivo salvo em %s", output_path)
    return output_path
