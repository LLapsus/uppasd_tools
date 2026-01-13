##########################################################################################
# analyze.py
#
# Functions for analyzing UppASD output data.
#
##########################################################################################

from __future__ import annotations

import fnmatch
import logging
import re
from pathlib import Path

import pandas as pd

from .uppout import UppOut

##########################################################################################

logger = logging.getLogger(__name__)

TEMPERATURE_RE = re.compile(r".*_T(\d+(?:\.\d+)?)$")
AVERAGES_PREFIX = "averages"

##########################################################################################

def scan_run_directories(root: str | Path) -> list[tuple[float, Path]]:
    """Scan immediate subdirectories under root and extract temperatures."""
    root_path = Path(root)
    runs: list[tuple[float, Path]] = []
    for entry in root_path.iterdir():
        if not entry.is_dir():
            continue
        match = TEMPERATURE_RE.match(entry.name)
        if not match:
            continue
        runs.append((float(match.group(1)), entry))
    return runs


def _extract_temperature_from_name(name: str) -> float:
    match = TEMPERATURE_RE.match(name)
    if not match:
        raise ValueError(f'Could not extract temperature from directory "{name}".')
    return float(match.group(1))


def _latest_averages_simid(run_dir: Path) -> str:
    latest_simid: str | None = None
    latest_mtime: float | None = None
    for entry in run_dir.iterdir():
        if not entry.is_file():
            continue
        parts = entry.name.split(".")
        if len(parts) != 3:
            continue
        if parts[0] != AVERAGES_PREFIX or parts[2] != "out":
            continue
        simid = parts[1]
        if len(simid) != 8:
            continue
        mtime = entry.stat().st_mtime
        if latest_simid is None or mtime > latest_mtime:
            latest_simid = simid
            latest_mtime = mtime
    if latest_simid is None:
        raise FileNotFoundError(
            f'No "{AVERAGES_PREFIX}.*.out" files found in "{run_dir}".'
        )
    return latest_simid


def read_averages_last_line(run_dir: str | Path) -> dict[str, float]:
    """Read the latest averages file in a run directory and parse its last line."""
    run_path = Path(run_dir)
    temperature = _extract_temperature_from_name(run_path.name)
    simid = _latest_averages_simid(run_path)
    uppout = UppOut(run_path, simid=simid)
    frame = uppout.read_averages()
    if frame.empty:
        raise ValueError(
            f'No data rows found in averages file for "{run_path}".'
        )
    last_row = frame.iloc[-1]
    return {
        "T": temperature,
        "Mx": float(last_row["Mx"]),
        "My": float(last_row["My"]),
        "Mz": float(last_row["Mz"]),
        "M": float(last_row["M"]),
        "M_std": float(last_row["M_stdv"]),
    }


def collect_averages(
    root: str | Path,
    pattern: str = "*_T*",
    strict: bool = True,
) -> pd.DataFrame:
    """Collect averages from all run directories under root."""
    root_path = Path(root)
    columns = ["T", "Mx", "My", "Mz", "M", "M_std"]
    rows: list[dict[str, float]] = []

    for entry in root_path.iterdir():
        if not entry.is_dir():
            continue
        if not fnmatch.fnmatch(entry.name, pattern):
            continue
        try:
            rows.append(read_averages_last_line(entry))
        except Exception as exc:
            if strict:
                raise
            logger.warning("Skipping run %s: %s", entry, exc)

    if not rows:
        return pd.DataFrame(columns=columns)

    frame = pd.DataFrame(rows, columns=columns)
    frame.sort_values("T", inplace=True)
    frame.reset_index(drop=True, inplace=True)
    return frame
