from pathlib import Path

import pandas as pd
import pytest

from cd_viabilidade.data_io import (
    load_cds_candidatos_csv,
    load_demanda_csv,
    load_localidades_csv,
)


def test_loaders_happy_path_and_persist_outputs(tmp_path: Path):
    demanda_path = tmp_path / "demanda.csv"
    localidades_path = tmp_path / "localidades.csv"
    cds_path = tmp_path / "cds.csv"
    output_dir = tmp_path / "outputs"

    pd.DataFrame(
        {
            "id": [" c1 "],
            "cidade": [" São Paulo "],
            "uf": ["sp"],
            "demanda": ["10"],
            "lat": ["-23.55"],
            "lon": ["-46.63"],
        }
    ).to_csv(demanda_path, index=False)

    pd.DataFrame(
        {
            "id": [" l1 "],
            "cidade": [" Campinas "],
            "uf": ["sp"],
            "lat": ["-22.90"],
            "lon": ["-47.06"],
        }
    ).to_csv(localidades_path, index=False)

    pd.DataFrame(
        {
            "id": [" cd1 "],
            "cidade": [" Santos "],
            "uf": ["sp"],
            "lat": ["-23.96"],
            "lon": ["-46.33"],
            "custo_fixo": ["2500.50"],
        }
    ).to_csv(cds_path, index=False)

    demanda_df = load_demanda_csv(demanda_path, output_dir=output_dir)
    localidades_df = load_localidades_csv(localidades_path, output_dir=output_dir)
    cds_df = load_cds_candidatos_csv(cds_path, output_dir=output_dir)

    assert demanda_df.loc[0, "id"] == "c1"
    assert demanda_df.loc[0, "uf"] == "SP"
    assert demanda_df.loc[0, "demanda"] == 10
    assert locais_float(localidades_df.loc[0, "lat"]) == -22.9
    assert cds_df.loc[0, "custo_fixo"] == pytest.approx(2500.50)

    assert (output_dir / "demanda_normalizada.csv").exists()
    assert (output_dir / "localidades_normalizadas.csv").exists()
    assert (output_dir / "cds_candidatos_normalizados.csv").exists()


def locais_float(value: object) -> float:
    return float(value)


def test_missing_columns_raises_value_error(tmp_path: Path):
    demanda_path = tmp_path / "demanda_invalida.csv"
    pd.DataFrame(
        {
            "id": ["c1"],
            "cidade": ["São Paulo"],
            "uf": ["SP"],
            "lat": [-23.55],
            "lon": [-46.63],
        }
    ).to_csv(demanda_path, index=False)

    with pytest.raises(ValueError, match="Colunas ausentes"):
        load_demanda_csv(demanda_path, output_dir=tmp_path / "outputs")


def test_invalid_numeric_type_raises_value_error(tmp_path: Path):
    cds_path = tmp_path / "cds_invalido.csv"
    pd.DataFrame(
        {
            "id": ["cd1"],
            "cidade": ["Santos"],
            "uf": ["SP"],
            "lat": [-23.96],
            "lon": [-46.33],
            "custo_fixo": ["dois mil"],
        }
    ).to_csv(cds_path, index=False)

    with pytest.raises(ValueError, match="numérico inválido"):
        load_cds_candidatos_csv(cds_path, output_dir=tmp_path / "outputs")


def test_empty_dataset_raises_value_error(tmp_path: Path):
    locais_path = tmp_path / "localidades_vazio.csv"
    pd.DataFrame(columns=["id", "cidade", "uf", "lat", "lon"]).to_csv(locais_path, index=False)

    with pytest.raises(ValueError, match="está vazio"):
        load_localidades_csv(locais_path, output_dir=tmp_path / "outputs")
