from pathlib import Path

import pandas as pd

from cd_viabilidade.data_io import load_csv, require_columns, save_csv


def test_save_and_load_csv(tmp_path: Path):
    path = tmp_path / "a.csv"
    df = pd.DataFrame({"a": [1]})
    save_csv(df, path)
    loaded = load_csv(path)
    assert loaded.iloc[0, 0] == 1


def test_require_columns_error():
    df = pd.DataFrame({"a": [1]})
    try:
        require_columns(df, ["a", "b"])
    except ValueError:
        assert True
    else:
        assert False
