from __future__ import annotations

import pandas as pd
import pytest
from pandas.api.types import is_numeric_dtype

from uppasd_tools.uppout_schema import (
    AVERAGES_COLUMNS,
    COORD_COLUMNS,
    CUMULANTS_COLUMNS,
    PROJAVGS_COLUMNS,
    PROJCUMULANTS_COLUMNS,
    RESTART_COLUMNS,
    STRUCT_COLUMNS,
)


def _assert_numeric_columns(frame: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        assert is_numeric_dtype(frame[column]), f"{column} is not numeric"


def test_feco_counts(feco_uppout) -> None:
    coord = feco_uppout.read_coord()
    restart = feco_uppout.read_restart()

    assert feco_uppout.num_atoms == len(coord)
    assert feco_uppout.num_atoms_cell == coord["at_num_cell"].nunique()
    assert feco_uppout.num_atom_types == coord["at_type"].nunique()
    assert feco_uppout.num_ens == restart["ens_num"].nunique()

    assert feco_uppout.xrange == (float(coord["x"].min()), float(coord["x"].max()))
    assert feco_uppout.yrange == (float(coord["y"].min()), float(coord["y"].max()))
    assert feco_uppout.zrange == (float(coord["z"].min()), float(coord["z"].max()))


def test_feco_read_coord(feco_uppout) -> None:
    frame = feco_uppout.read_coord()
    assert list(frame.columns) == COORD_COLUMNS
    assert not frame.empty
    _assert_numeric_columns(frame, COORD_COLUMNS)


def test_feco_read_restart(feco_uppout) -> None:
    frame = feco_uppout.read_restart()
    assert list(frame.columns) == RESTART_COLUMNS
    assert not frame.empty
    _assert_numeric_columns(frame, RESTART_COLUMNS)


def test_feco_read_struct(feco_uppout) -> None:
    frame = feco_uppout.read_struct()
    assert list(frame.columns) == STRUCT_COLUMNS
    assert not frame.empty
    _assert_numeric_columns(frame, STRUCT_COLUMNS)


def test_feco_read_averages(feco_uppout) -> None:
    frame = feco_uppout.read_averages()
    assert list(frame.columns) == AVERAGES_COLUMNS
    assert not frame.empty
    _assert_numeric_columns(frame, AVERAGES_COLUMNS)


def test_feco_read_cumulants(feco_uppout) -> None:
    frame = feco_uppout.read_cumulants()
    assert list(frame.columns) == CUMULANTS_COLUMNS
    assert not frame.empty
    _assert_numeric_columns(frame, CUMULANTS_COLUMNS)


def test_feco_read_energy_missing_std(feco_uppout) -> None:
    with pytest.raises(FileNotFoundError):
        feco_uppout.read_energy()


def test_feco_read_projavgs(feco_uppout) -> None:
    frames = feco_uppout.read_projavgs()
    assert frames
    for proj, frame in frames.items():
        assert isinstance(proj, int)
        assert list(frame.columns) == PROJAVGS_COLUMNS
        assert not frame.empty
        _assert_numeric_columns(frame, PROJAVGS_COLUMNS)


def test_feco_read_projcumulants(feco_uppout) -> None:
    frames = feco_uppout.read_projcumulants()
    assert frames
    for proj, frame in frames.items():
        assert isinstance(proj, int)
        assert list(frame.columns) == PROJCUMULANTS_COLUMNS
        assert not frame.empty
        _assert_numeric_columns(frame, PROJCUMULANTS_COLUMNS)


def test_feco_final_configs(feco_uppout) -> None:
    configs = feco_uppout.final_configs()
    assert len(configs) == feco_uppout.num_ens
    for config in configs:
        assert not config.empty
        for column in ("x", "y", "z", "at_type", "mx", "my", "mz"):
            assert column in config.columns
        _assert_numeric_columns(config, ["x", "y", "z", "mx", "my", "mz"])
