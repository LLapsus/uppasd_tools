##########################################################################################
# analyze.py
#
# Functions for analyzing UppASD output data.
#
##########################################################################################

from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

from .uppout import UppOut

##########################################################################################

logger = logging.getLogger(__name__)

AVERAGES_PREFIX = "averages"
TEMPLATE_FIELD_RE = re.compile(r"{([A-Za-z_][A-Za-z0-9_]*)}")
INT_RE = re.compile(r"^-?\d+$")
FLOAT_RE = re.compile(r"^-?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][+-]?\d+)?$")

##########################################################################################

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


def _compile_name_template(template: str) -> tuple[re.Pattern[str], list[str]]:
    fields = [match.group(1) for match in TEMPLATE_FIELD_RE.finditer(template)]
    if not fields:
        raise ValueError("Template must include at least one {field} placeholder.")
    if len(set(fields)) != len(fields):
        raise ValueError("Template placeholders must be unique.")

    pattern_parts: list[str] = ["^"]
    last_end = 0
    for match in TEMPLATE_FIELD_RE.finditer(template):
        pattern_parts.append(re.escape(template[last_end:match.start()]))
        field = match.group(1)
        pattern_parts.append(f"(?P<{field}>[^/]+)")
        last_end = match.end()
    pattern_parts.append(re.escape(template[last_end:]))
    pattern_parts.append("$")

    return re.compile("".join(pattern_parts)), fields


def _coerce_template_value(value: str) -> float | int | str:
    if INT_RE.match(value):
        return int(value)
    if FLOAT_RE.match(value):
        return float(value)
    return value


def _read_averages_last_row(run_dir: str | Path) -> dict[str, float]:
    run_path = Path(run_dir)
    simid = _latest_averages_simid(run_path)
    uppout = UppOut(run_path, simid=simid)
    frame = uppout.read_averages()
    if frame.empty:
        raise ValueError(
            f'No data rows found in averages file for "{run_path}".'
        )
    last_row = frame.iloc[-1]
    return {
        "Mx": float(last_row["Mx"]),
        "My": float(last_row["My"]),
        "Mz": float(last_row["Mz"]),
        "M": float(last_row["M"]),
        "M_std": float(last_row["M_stdv"]),
    }


def collect_averages(
    root: str | Path,
    name_template: str,
    strict: bool = True,
) -> pd.DataFrame:
    """Collect averages from run directories matching a name template."""
    root_path = Path(root)
    name_pattern, fields = _compile_name_template(name_template)
    columns = fields + ["Mx", "My", "Mz", "M", "M_std"]
    rows: list[dict[str, float | int | str]] = []

    for entry in root_path.iterdir():
        if not entry.is_dir():
            continue
        match = name_pattern.match(entry.name)
        if not match:
            continue
        try:
            variables = {
                key: _coerce_template_value(value)
                for key, value in match.groupdict().items()
            }
            averages = _read_averages_last_row(entry)
            row = {**variables, **averages}
            rows.append(row)
        except Exception as exc:
            if strict:
                raise
            logger.warning("Skipping run %s: %s", entry, exc)

    if not rows:
        return pd.DataFrame(columns=columns)

    frame = pd.DataFrame(rows, columns=columns)
    frame.sort_values(fields, inplace=True)
    frame.reset_index(drop=True, inplace=True)
    return frame
