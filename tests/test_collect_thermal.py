from __future__ import annotations

from pathlib import Path

import numpy as np

from uppasd_tools.collect import collect_averages, collect_cumulants
from uppasd_tools.uppout import UppOut
from uppasd_tools.uppout_schema import AVERAGES_COLUMNS, CUMULANTS_COLUMNS


def _count_matching_dirs(root: Path, prefix: str) -> int:
    return len([entry for entry in root.iterdir() if entry.is_dir() and entry.name.startswith(prefix)])


def test_collect_averages_bccfe_thermal(data_dir: Path) -> None:
    root = data_dir / "bccFe_thermal"
    frame = collect_averages(
        root,
        name_template="bccFe_temp_T{T}",
        progress=False,
    )
    assert not frame.empty
    expected_columns = ["T"] + [
        "M_std" if col == "M_stdv" else col
        for col in AVERAGES_COLUMNS
        if col != "iter"
    ]
    assert list(frame.columns) == expected_columns
    assert len(frame) == _count_matching_dirs(root, "bccFe_temp_T")
    for col in expected_columns[1:]:
        assert frame[col].notna().all()


def test_collect_cumulants_bccfe_thermal(data_dir: Path) -> None:
    root = data_dir / "bccFe_thermal"
    frame = collect_cumulants(
        root,
        name_template="bccFe_temp_T{T}",
        progress=False,
    )
    assert not frame.empty
    expected_columns = ["T"] + [
        col for col in CUMULANTS_COLUMNS if col != "iter"
    ]
    assert list(frame.columns) == expected_columns
    assert len(frame) == _count_matching_dirs(root, "bccFe_temp_T")
    for col in expected_columns[1:]:
        assert frame[col].notna().all()


def test_collect_averages_slice_matches_manual(data_dir: Path) -> None:
    root = data_dir / "bccFe_thermal"
    run_dir = root / "bccFe_temp_T100"

    uppout = UppOut(run_dir)
    frame = uppout.read_averages()
    slice_rows = frame.iloc[slice(10, 50, 2)]
    mean_columns = [col for col in AVERAGES_COLUMNS if col != "iter"]
    output_columns = [
        "M_std" if col == "M_stdv" else col for col in mean_columns
    ]
    manual = slice_rows[mean_columns].mean()

    collected = collect_averages(
        root,
        name_template="bccFe_temp_T{T}",
        start=10,
        end=50,
        step=2,
        progress=False,
    )
    row = collected.loc[collected["T"] == 100].iloc[0]

    for col, out_col in zip(mean_columns, output_columns):
        assert np.isclose(row[out_col], float(manual[col]), rtol=1e-8, atol=1e-12)


def test_collect_averages_no_matches(data_dir: Path) -> None:
    root = data_dir / "bccFe_thermal"
    frame = collect_averages(
        root,
        name_template="does_not_exist_T{T}",
        progress=False,
    )
    expected_columns = ["T"] + [
        "M_std" if col == "M_stdv" else col
        for col in AVERAGES_COLUMNS
        if col != "iter"
    ]
    assert list(frame.columns) == expected_columns
    assert frame.empty
