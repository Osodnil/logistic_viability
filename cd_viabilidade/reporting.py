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
    required = {"base", "1_novo_cd", "2_novos_cds"}
    missing = required.difference(scenario_costs) | required.difference(scenario_indicators)
    if missing:
        raise ValueError(f"Cenários obrigatórios ausentes para relatório executivo: {sorted(missing)}")

    base_cost = scenario_costs["base"]
    cost_1 = scenario_costs["1_novo_cd"]
    cost_2 = scenario_costs["2_novos_cds"]

    cost_delta_1 = base_cost - cost_1
    cost_delta_2 = base_cost - cost_2

    base_ind = scenario_indicators["base"]
    one_ind = scenario_indicators["1_novo_cd"]
    two_ind = scenario_indicators["2_novos_cds"]

    recommendation = "Manter cenário base"
    if one_ind.npv > base_ind.npv and one_ind.npv >= two_ind.npv:
        recommendation = "Avançar com abertura de 1 novo CD"
    elif two_ind.npv > base_ind.npv and two_ind.npv > one_ind.npv:
        recommendation = "Avançar com abertura de 2 novos CDs"

    content = "\n".join(
        [
            "# Relatório Executivo de Viabilidade",
            "",
            "## Resumo dos cenários",
            f"- base: custo anual {base_cost:.2f}",
            f"- 1_novo_cd: custo anual {cost_1:.2f}",
            f"- 2_novos_cds: custo anual {cost_2:.2f}",
            "",
            "## Custos comparativos",
            f"- Redução anual estimada com 1 novo CD vs base: {cost_delta_1:.2f}",
            f"- Redução anual estimada com 2 novos CDs vs base: {cost_delta_2:.2f}",
            "",
            "## Indicadores financeiros",
            f"- base: VPL={base_ind.npv:.2f}, Payback={_format_payback(base_ind.payback_simple)}, "
            f"Payback descontado={_format_payback(base_ind.payback_discounted)}, ROI={base_ind.roi:.2%}",
            f"- 1_novo_cd: VPL={one_ind.npv:.2f}, Payback={_format_payback(one_ind.payback_simple)}, "
            f"Payback descontado={_format_payback(one_ind.payback_discounted)}, ROI={one_ind.roi:.2%}",
            f"- 2_novos_cds: VPL={two_ind.npv:.2f}, Payback={_format_payback(two_ind.payback_simple)}, "
            f"Payback descontado={_format_payback(two_ind.payback_discounted)}, ROI={two_ind.roi:.2%}",
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
