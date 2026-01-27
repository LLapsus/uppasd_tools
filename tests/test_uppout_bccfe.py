from __future__ import annotations

import pandas as pd
from pandas.api.types import is_numeric_dtype

from uppasd_tools.uppout_schema import (
    AVERAGES_COLUMNS,
    COORD_COLUMNS,
    CUMULANTS_COLUMNS,
    ENERGY_COLUMNS,
    RESTART_COLUMNS,
    STRUCT_COLUMNS,
)


def _assert_numeric_columns(frame: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        assert is_numeric_dtype(frame[column]), f"{column} is not numeric"


def test_bccfe_counts(bccfe_uppout) -> None:
    coord = bccfe_uppout.read_coord()
    restart = bccfe_uppout.read_restart()

    assert bccfe_uppout.num_atoms == len(coord)
    assert bccfe_uppout.num_atoms_cell == coord["at_num_cell"].nunique()
    assert bccfe_uppout.num_atom_types == coord["at_type"].nunique()
    assert bccfe_uppout.num_ens == restart["ens_num"].nunique()

    assert bccfe_uppout.xrange == (float(coord["x"].min()), float(coord["x"].max()))
    assert bccfe_uppout.yrange == (float(coord["y"].min()), float(coord["y"].max()))
    assert bccfe_uppout.zrange == (float(coord["z"].min()), float(coord["z"].max()))


def test_bccfe_read_coord(bccfe_uppout) -> None:
    frame = bccfe_uppout.read_coord()
    assert list(frame.columns) == COORD_COLUMNS
    assert not frame.empty
    _assert_numeric_columns(frame, COORD_COLUMNS)


def test_bccfe_read_restart(bccfe_uppout) -> None:
    frame = bccfe_uppout.read_restart()
    assert list(frame.columns) == RESTART_COLUMNS
    assert not frame.empty
    _assert_numeric_columns(frame, RESTART_COLUMNS)


def test_bccfe_read_struct(bccfe_uppout) -> None:
    frame = bccfe_uppout.read_struct()
    assert list(frame.columns) == STRUCT_COLUMNS
    assert not frame.empty
    _assert_numeric_columns(frame, STRUCT_COLUMNS)


def test_bccfe_read_averages(bccfe_uppout) -> None:
    frame = bccfe_uppout.read_averages()
    assert list(frame.columns) == AVERAGES_COLUMNS
    assert not frame.empty
    _assert_numeric_columns(frame, AVERAGES_COLUMNS)


def test_bccfe_read_cumulants(bccfe_uppout) -> None:
    frame = bccfe_uppout.read_cumulants()
    assert list(frame.columns) == CUMULANTS_COLUMNS
    assert not frame.empty
    _assert_numeric_columns(frame, CUMULANTS_COLUMNS)


def test_bccfe_read_energy(bccfe_uppout) -> None:
    frame = bccfe_uppout.read_energy()
    assert not frame.empty

    std_columns = [f"{column}_std" for column in ENERGY_COLUMNS if column != "iter"]
    expected_columns = ENERGY_COLUMNS + std_columns
    for column in expected_columns:
        assert column in frame.columns

    _assert_numeric_columns(frame, expected_columns)


def test_bccfe_final_configs(bccfe_uppout) -> None:
    configs = bccfe_uppout.final_configs()
    assert len(configs) == bccfe_uppout.num_ens
    for config in configs:
        assert not config.empty
        for column in ("x", "y", "z", "at_type", "mx", "my", "mz"):
            assert column in config.columns
        _assert_numeric_columns(config, ["x", "y", "z", "mx", "my", "mz"])
