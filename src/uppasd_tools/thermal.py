from __future__ import annotations

import fnmatch
import logging
import re
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

TEMPERATURE_RE = re.compile(r".*_T(\d+(?:\.\d+)?)$")
COMMENT_PREFIXES = ("#", "!", ";")
AVERAGES_PREFIX = "averages"


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


def _latest_averages_file(run_dir: Path) -> Path:
    averages_files = list(run_dir.glob(f"{AVERAGES_PREFIX}*"))
    if not averages_files:
        raise FileNotFoundError(
            f'No "{AVERAGES_PREFIX}*" files found in "{run_dir}".'
        )
    return max(averages_files, key=lambda path: path.stat().st_mtime)


def _read_last_data_line(path: Path) -> str:
    lines = path.read_text().splitlines()
    for line in reversed(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(COMMENT_PREFIXES):
            continue
        return stripped
    raise ValueError(f'No data lines found in "{path}".')


def _parse_averages_line(line: str) -> dict[str, float]:
    parts = line.split()
    if len(parts) != 6:
        raise ValueError(
            "Expected 6 columns (step + 5 floats) in averages line."
        )
    try:
        int(parts[0])
    except ValueError as exc:
        raise ValueError("Step column is not an integer.") from exc
    try:
        values = [float(value) for value in parts[1:]]
    except ValueError as exc:
        raise ValueError("One or more averages columns are not floats.") from exc
    return {
        "Mx": values[0],
        "My": values[1],
        "Mz": values[2],
        "M": values[3],
        "M_std": values[4],
    }


def read_averages_last_line(run_dir: str | Path) -> dict[str, float]:
    """Read the latest averages file in a run directory and parse its last line."""
    run_path = Path(run_dir)
    temperature = _extract_temperature_from_name(run_path.name)
    latest_file = _latest_averages_file(run_path)
    last_line = _read_last_data_line(latest_file)
    parsed = _parse_averages_line(last_line)
    parsed["T"] = temperature
    return parsed


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
