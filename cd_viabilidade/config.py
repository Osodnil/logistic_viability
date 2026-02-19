"""Configurações centrais da aplicação."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Configuração da aplicação com caminhos e parâmetros padrão."""

    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = base_dir / "data"
    output_dir: Path = base_dir / "outputs"
    default_facility_limit: int = 2
    default_unit_revenue: float = 150.0
