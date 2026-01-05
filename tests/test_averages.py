from __future__ import annotations

from pathlib import Path

import pandas as pd

from uppasd_tools.averages import collect_averages, read_averages_last_line, scan_run_directories


def _write_averages_file(path: Path, line: str) -> None:
    path.write_text(
        "\n".join(
            [
                "# header",
                "1000 0 0 0 0 0",
                "",
                line,
            ]
        )
    )


def test_scan_run_directories_extracts_temperatures(tmp_path: Path) -> None:
    root = tmp_path / "Test_sym0"
    root.mkdir()
    (root / "SmCo5fi01_sym0_T300").mkdir()
    (root / "SmCo5fi01_sym0_T400_suffix").mkdir()
    (root / "unrelated").mkdir()

    runs = scan_run_directories(root)
    temps = sorted(temp for temp, _ in runs)

    assert temps == [300.0, 400.0]


def test_read_averages_last_line_scientific_notation(tmp_path: Path) -> None:
    run_dir = tmp_path / "SmCo5fi01_sym0_T50"
    run_dir.mkdir()
    averages_path = run_dir / "averages"
    line = "599900  2.40736381E-03  2.62769943E-03  3.25060379E-03  9.86414440E-03  1.92715641E-03"
    _write_averages_file(averages_path, line)

    result = read_averages_last_line(run_dir)

    assert result["T"] == 50.0
    assert result["Mx"] == 2.40736381e-03
    assert result["My"] == 2.62769943e-03
    assert result["Mz"] == 3.25060379e-03
    assert result["M"] == 9.86414440e-03
    assert result["M_std"] == 1.92715641e-03


def test_collect_averages_strict_false_skips_bad_runs(tmp_path: Path, caplog) -> None:
    root = tmp_path / "Test_sym0"
    root.mkdir()

    good_run = root / "SmCo5fi01_sym0_T100"
    good_run.mkdir()
    _write_averages_file(
        good_run / "averages",
        "10 1.0 2.0 3.0 4.0 5.0",
    )

    bad_run = root / "SmCo5fi01_sym0_T200"
    bad_run.mkdir()

    with caplog.at_level("WARNING"):
        frame = collect_averages(root, strict=False)

    assert isinstance(frame, pd.DataFrame)
    assert list(frame["T"]) == [100.0]
    assert any("Skipping run" in record.message for record in caplog.records)
