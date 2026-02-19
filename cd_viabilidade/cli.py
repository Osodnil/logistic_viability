"""Interface de linha de comando para pipeline de viabilidade."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .auto_costs import estimate_fixed_costs
from .config import AppConfig
from .cost_matrix import build_cost_matrix
from .data_io import load_csv
from .facility_location import solve_facility_location
from .financials import calculate_financial_indicators, compute_financials
from .logging_config import configure_logging
from .mapping import build_map
from .reporting import generate_executive_report, write_markdown_report
from .scenarios import DEFAULT_SCENARIOS, ScenarioConfig, run_scenarios_batch

logger = configure_logging(logger_name=__name__)


def _demand_column(df: pd.DataFrame) -> str:
    return "demanda" if "demanda" in df.columns else "demand"


def _resolve_fixed_costs(config: AppConfig, facilities: pd.DataFrame) -> pd.DataFrame:
    fixed_costs_path = config.data_dir / "fixed_costs.csv"
    regional_costs_path = config.data_dir / "regional_costs.csv"

    if fixed_costs_path.exists():
        return load_csv(fixed_costs_path)
    if regional_costs_path.exists():
        regional_costs = load_csv(regional_costs_path)
        fixed_costs = estimate_fixed_costs(facilities, regional_costs)
        config.output_dir.mkdir(parents=True, exist_ok=True)
        fixed_costs.to_csv(config.output_dir / "fixed_costs_estimados.csv", index=False)
        return fixed_costs
    raise FileNotFoundError("Forneça data/fixed_costs.csv ou data/regional_costs.csv para estimar custos")


def _resolve_facility_groups(facilities: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Retorna (existing, candidates) com base em `is_existing` quando disponível."""
    if "is_existing" not in facilities.columns:
        all_ids = facilities["facility_id"].astype(str).tolist()
        return [], all_ids

    flags = facilities["is_existing"].astype(str).str.lower().map({"1": True, "true": True, "yes": True, "sim": True})
    is_existing = flags.astype("boolean").fillna(False)

    existing = facilities.loc[is_existing, "facility_id"].astype(str).tolist()
    candidates = facilities.loc[~is_existing, "facility_id"].astype(str).tolist()
    return existing, candidates


def execute_scenario(config: AppConfig, scenario_name: str = "base", scenario: ScenarioConfig | None = None) -> dict:
    """Executa cenário único, salva artefatos e retorna resumo."""
    scenario_cfg = scenario or DEFAULT_SCENARIOS.get(scenario_name, ScenarioConfig())

    facilities = load_csv(config.data_dir / "facilities.csv")
    clients = load_csv(config.data_dir / "clients.csv")
    fixed_costs = _resolve_fixed_costs(config, facilities)

    demand_col = _demand_column(clients)
    scenario_clients = clients.copy()
    scenario_clients["demanda"] = scenario_clients[demand_col].astype(float) * (1 + scenario_cfg.crescimento_demanda)

    cost_matrix = build_cost_matrix(
        facilities,
        scenario_clients,
        scenario_params={
            "tributacao": scenario_cfg.fator_tributario,
            "salario_logistica": scenario_cfg.fator_salarial,
        },
    )

    existing, candidates = _resolve_facility_groups(facilities)

    if scenario_name == "base" and existing:
        max_new = 0
        min_total_open = len(existing)
    elif scenario_cfg.limite_novos_cds is not None and existing:
        max_new = scenario_cfg.limite_novos_cds
        min_total_open = len(existing) + scenario_cfg.limite_novos_cds
    else:
        max_new = scenario_cfg.limite_novos_cds or config.default_facility_limit
        min_total_open = None

    result = solve_facility_location(
        cost_matrix,
        fixed_costs,
        max_new_facilities=max_new,
        forced_open_facilities=existing,
        candidate_facilities=candidates,
        min_total_open_facilities=min_total_open,
    )
    assignments = pd.DataFrame(
        [{"client_id": client, "facility_id": facility} for client, facility in result.allocation.items()]
    )
    summary = compute_financials(assignments, cost_matrix, config.default_unit_revenue, result.fixed_cost)

    scenario_slug = scenario_name.replace(" ", "_")
    map_path = build_map(
        facilities,
        scenario_clients,
        config.output_dir / f"mapa_{scenario_slug}.html",
        selected_facilities=result.open_facilities,
        assignments=assignments,
    )
    report_path = write_markdown_report(
        config.output_dir / f"relatorio_{scenario_slug}.md",
        result.open_facilities,
        summary,
        result.total_cost,
    )
    assignments.to_csv(config.output_dir / f"assignments_{scenario_slug}.csv", index=False)

    return {
        "scenario": scenario_name,
        "selected_facilities": result.open_facilities,
        "total_cost": result.total_cost,
        "fixed_cost": result.fixed_cost,
        "variable_cost": result.variable_cost,
        "report": str(report_path),
        "map": str(map_path),
    }


def run_pipeline(config: AppConfig, scenario_name: str = "base") -> dict:
    """Executa pipeline completo para um cenário."""
    out = execute_scenario(config=config, scenario_name=scenario_name)
    logger.info("Pipeline executado com sucesso no cenário %s", scenario_name)
    return out


def run_scenarios(config: AppConfig) -> pd.DataFrame:
    """Executa cenários em lote e salva comparativo."""
    facilities = load_csv(config.data_dir / "facilities.csv")
    clients = load_csv(config.data_dir / "clients.csv")

    comparative = run_scenarios_batch(facilities, clients, DEFAULT_SCENARIOS)
    output_path = config.output_dir / "comparativo_cenarios.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    comparative.to_csv(output_path, index=False)

    for scenario_name in DEFAULT_SCENARIOS:
        execute_scenario(config, scenario_name)

    logger.info("Comparativo de cenários salvo em %s", output_path)
    return comparative


def generate_report(config: AppConfig) -> Path:
    """Gera relatório executivo consolidando todos os cenários configurados."""
    scenario_outputs = {name: execute_scenario(config, name) for name in DEFAULT_SCENARIOS}

    horizon = 5
    rate = 0.12
    baseline = scenario_outputs["base"]["total_cost"]
    scenario_costs = {name: data["total_cost"] for name, data in scenario_outputs.items()}
    scenario_indicators = {
        name: calculate_financial_indicators(
            initial_investment=data["fixed_cost"],
            annual_savings=baseline - data["total_cost"],
            horizon_years=horizon,
            discount_rate=rate,
        )
        for name, data in scenario_outputs.items()
    }

    return generate_executive_report(scenario_costs, scenario_indicators, output_dir=config.output_dir)


def build_parser() -> argparse.ArgumentParser:
    """Cria parser de argumentos do CLI."""
    parser = argparse.ArgumentParser(description="Pipeline de viabilidade logística")
    parser.add_argument("--data-dir", type=Path, default=AppConfig().data_dir)
    parser.add_argument("--output-dir", type=Path, default=AppConfig().output_dir)
    parser.add_argument("--facility-limit", type=int, default=AppConfig().default_facility_limit)
    parser.add_argument("--unit-revenue", type=float, default=AppConfig().default_unit_revenue)

    subparsers = parser.add_subparsers(dest="command", required=True)

    run_pipeline_parser = subparsers.add_parser("run-pipeline", help="Executa cenário único")
    run_pipeline_parser.add_argument("--scenario", default="base")

    subparsers.add_parser("run-scenarios", help="Executa lote de cenários")
    subparsers.add_parser("generate-report", help="Gera relatório executivo")
    subparsers.add_parser("serve-api", help="Mostra comando para iniciar API")

    return parser


def main() -> None:
    """Ponto de entrada do CLI."""
    args = build_parser().parse_args()
    config = AppConfig(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        default_facility_limit=args.facility_limit,
        default_unit_revenue=args.unit_revenue,
    )

    if args.command == "run-pipeline":
        result = run_pipeline(config, scenario_name=args.scenario)
        print(pd.Series(result).to_string())
    elif args.command == "run-scenarios":
        df = run_scenarios(config)
        print(df.to_string(index=False))
    elif args.command == "generate-report":
        report_path = generate_report(config)
        print(f"Relatório gerado em: {report_path}")
    elif args.command == "serve-api":
        print("uvicorn cd_viabilidade.api:app --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    main()
