"""Funções de leitura, validação e persistência de datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from .logging_config import configure_logging

logger = configure_logging(logger_name=__name__)


PathLike = str | Path

REQUIRED_DEMANDA_COLUMNS = ("id", "cidade", "uf", "demanda", "lat", "lon")
REQUIRED_LOCALIDADES_COLUMNS = ("id", "cidade", "uf", "lat", "lon")
REQUIRED_CDS_COLUMNS = ("id", "cidade", "uf", "lat", "lon", "custo_fixo")

STRING_COLUMNS = ("id", "cidade", "uf")
NUMERIC_COLUMNS = ("demanda", "lat", "lon", "custo_fixo")


def load_csv(path: PathLike) -> pd.DataFrame:
    """Carrega um CSV em :class:`pandas.DataFrame`."""
    path = Path(path)
    logger.info("Carregando CSV: %s", path)
    return pd.read_csv(path)



def save_csv(df: pd.DataFrame, path: PathLike) -> None:
    """Salva um DataFrame em CSV."""
    path = Path(path)
    logger.info("Salvando CSV: %s", path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)



def require_columns(df: pd.DataFrame, required: Iterable[str]) -> None:
    """Valida se todas as colunas obrigatórias existem."""
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"Colunas ausentes: {missing}")



def _ensure_not_empty(df: pd.DataFrame, dataset_name: str) -> None:
    if df.empty:
        raise ValueError(f"Dataset '{dataset_name}' está vazio")



def _normalize_string_columns(df: pd.DataFrame, columns: Iterable[str], dataset_name: str) -> None:
    for col in columns:
        if col not in df.columns:
            continue
        if not pd.api.types.is_object_dtype(df[col]) and not pd.api.types.is_string_dtype(df[col]):
            raise ValueError(
                f"Coluna '{col}' do dataset '{dataset_name}' tem tipo inválido para string: {df[col].dtype}"
            )
        df[col] = df[col].astype("string").str.strip()
        if col == "uf":
            df[col] = df[col].str.upper()



def _normalize_numeric_columns(df: pd.DataFrame, columns: Iterable[str], dataset_name: str) -> None:
    for col in columns:
        if col not in df.columns:
            continue
        try:
            df[col] = pd.to_numeric(df[col], errors="raise")
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Coluna '{col}' do dataset '{dataset_name}' possui valor/tipo numérico inválido"
            ) from exc



def normalize_dataframe(df: pd.DataFrame, *, dataset_name: str) -> pd.DataFrame:
    """Normaliza tipos numéricos e strings de um DataFrame."""
    normalized = df.copy()
    _normalize_string_columns(normalized, STRING_COLUMNS, dataset_name)
    _normalize_numeric_columns(normalized, NUMERIC_COLUMNS, dataset_name)
    return normalized



def persist_intermediate_output(df: pd.DataFrame, filename: str, output_dir: PathLike = "outputs") -> Path:
    """Persiste um output intermediário no diretório ``outputs/``."""
    output_path = Path(output_dir) / filename
    save_csv(df, output_path)
    return output_path



def _load_typed_dataset(
    path: PathLike,
    *,
    dataset_name: str,
    required_columns: Iterable[str],
    output_filename: str,
    output_dir: PathLike = "outputs",
) -> pd.DataFrame:
    df = load_csv(path)
    _ensure_not_empty(df, dataset_name)
    require_columns(df, required_columns)
    normalized = normalize_dataframe(df, dataset_name=dataset_name)
    persist_intermediate_output(normalized, output_filename, output_dir)
    return normalized



def load_demanda_csv(path: PathLike, output_dir: PathLike = "outputs") -> pd.DataFrame:
    """Carrega e valida CSV de demanda."""
    return _load_typed_dataset(
        path,
        dataset_name="demanda",
        required_columns=REQUIRED_DEMANDA_COLUMNS,
        output_filename="demanda_normalizada.csv",
        output_dir=output_dir,
    )



def load_localidades_csv(path: PathLike, output_dir: PathLike = "outputs") -> pd.DataFrame:
    """Carrega e valida CSV de localidades."""
    return _load_typed_dataset(
        path,
        dataset_name="localidades",
        required_columns=REQUIRED_LOCALIDADES_COLUMNS,
        output_filename="localidades_normalizadas.csv",
        output_dir=output_dir,
    )



def load_cds_candidatos_csv(path: PathLike, output_dir: PathLike = "outputs") -> pd.DataFrame:
    """Carrega e valida CSV de CDs candidatos."""
    return _load_typed_dataset(
        path,
        dataset_name="cds_candidatos",
        required_columns=REQUIRED_CDS_COLUMNS,
        output_filename="cds_candidatos_normalizados.csv",
        output_dir=output_dir,
    )
