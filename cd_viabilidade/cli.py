"""Interface de linha de comando para pipeline de viabilidade."""

import argparse
from pathlib import Path

import pandas as pd

from .config import AppConfig
from .cost_matrix import build_cost_matrix
from .data_io import load_csv
from .facility_location import solve_facility_location
from .financials import compute_financials
from .logging_config import configure_logging
from .mapping import build_map
from .reporting import write_markdown_report

logger = configure_logging(logger_name=__name__)


def run_pipeline(config: AppConfig) -> dict:
    """Executa pipeline completo e retorna artefatos."""
    facilities = load_csv(config.data_dir / "facilities.csv")
    clients = load_csv(config.data_dir / "clients.csv")
    fixed_costs = load_csv(config.data_dir / "fixed_costs.csv")

    matrix = build_cost_matrix(facilities, clients)
    selected, assignments, total_cost = solve_facility_location(matrix, fixed_costs, config.default_facility_limit)
    fixed_selected = float(
        fixed_costs.loc[fixed_costs["facility_id"].isin(selected), "fixed_cost"].sum()
    )
    summary = compute_financials(assignments, matrix, config.default_unit_revenue, fixed_selected)

    map_path = build_map(facilities, clients, config.output_dir / "mapa.html")
    report_path = write_markdown_report(config.output_dir / "relatorio.md", selected, summary, total_cost)

    assignments.to_csv(config.output_dir / "assignments.csv", index=False)
    logger.info("Pipeline executado com sucesso")
    return {
        "selected_facilities": selected,
        "total_cost": total_cost,
        "report": str(report_path),
        "map": str(map_path),
    }


def build_parser() -> argparse.ArgumentParser:
    """Cria parser de argumentos do CLI."""
    parser = argparse.ArgumentParser(description="Pipeline de viabilidade logística")
    parser.add_argument("--data-dir", type=Path, default=AppConfig().data_dir)
    parser.add_argument("--output-dir", type=Path, default=AppConfig().output_dir)
    parser.add_argument("--facility-limit", type=int, default=AppConfig().default_facility_limit)
    parser.add_argument("--unit-revenue", type=float, default=AppConfig().default_unit_revenue)
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
    result = run_pipeline(config)
    print(pd.Series(result).to_string())


if __name__ == "__main__":
    main()
