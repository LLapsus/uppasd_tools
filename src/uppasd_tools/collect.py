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

TEMPLATE_FIELD_RE = re.compile(r"{([A-Za-z_][A-Za-z0-9_]*)}")
INT_RE = re.compile(r"^-?\d+$")
FLOAT_RE = re.compile(r"^-?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][+-]?\d+)?$")

##########################################################################################

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


def _read_averages_mean(
    run_dir: str | Path,
    simid: str | None = None,
    start: int | None = None,
    end: int | None = None,
    step: int | None = None,
) -> dict[str, float]:
    run_path = Path(run_dir)
    uppout = UppOut(run_path, simid=simid) if simid else UppOut(run_path)
    frame = uppout.read_averages()
    if frame.empty:
        raise ValueError(
            f'No data rows found in averages file for "{run_path}".'
        )
    slice_rows = frame.iloc[slice(start, end, step)]
    if slice_rows.empty:
        raise ValueError(
            f'No data rows found in selected range for "{run_path}".'
        )
    mean_row = slice_rows[["Mx", "My", "Mz", "M", "M_stdv"]].mean()
    return {
        "Mx": float(mean_row["Mx"]),
        "My": float(mean_row["My"]),
        "Mz": float(mean_row["Mz"]),
        "M": float(mean_row["M"]),
        "M_std": float(mean_row["M_stdv"]),
    }


def _read_cumulants_mean(
    run_dir: str | Path,
    simid: str | None = None,
    start: int | None = None,
    end: int | None = None,
    step: int | None = None,
) -> dict[str, float]:
    run_path = Path(run_dir)
    uppout = UppOut(run_path, simid=simid) if simid else UppOut(run_path)
    frame = uppout.read_cumulants()
    if frame.empty:
        raise ValueError(
            f'No data rows found in cumulants file for "{run_path}".'
        )
    slice_rows = frame.iloc[slice(start, end, step)]
    if slice_rows.empty:
        raise ValueError(
            f'No data rows found in selected range for "{run_path}".'
        )
    mean_row = slice_rows[
        [
            "M",
            "M2",
            "M4",
            "Binder",
            "chi",
            "Cv",
            "E",
            "E_exch",
            "E_lsf",
        ]
    ].mean()
    return {
        "M": float(mean_row["M"]),
        "M2": float(mean_row["M2"]),
        "M4": float(mean_row["M4"]),
        "Binder": float(mean_row["Binder"]),
        "chi": float(mean_row["chi"]),
        "Cv": float(mean_row["Cv"]),
        "E": float(mean_row["E"]),
        "E_exch": float(mean_row["E_exch"]),
        "E_lsf": float(mean_row["E_lsf"]),
    }


def collect_averages(
    root: str | Path,
    name_template: str,
    simid: str | None = None,
    start: int | None = None,
    end: int | None = None,
    step: int | None = None,
    strict: bool = True,
) -> pd.DataFrame:
    """
    Collect averaged output columns from run directories matching a name template.

    Parameters:
        root: Directory containing run subdirectories.
        name_template: Folder name template with `{field}` placeholders used to
            extract variables into columns (e.g., "run_T{T}_P{P}").
        simid: Optional UppASD simid to select a specific output set within each
            run directory. When None, UppOut auto-detects the simid.
        start: Start index for row slicing (inclusive) before averaging.
        end: End index for row slicing (exclusive) before averaging.
        step: Step for row slicing before averaging.
        strict: When True, raise on any bad run; when False, skip with a warning.

    Returns:
        DataFrame containing one row per run directory. Columns include the
        extracted template variables and the averaged values for 
        `Mx`, `My`, `Mz`, `M`, and `M_std`.
    """
    root_path = Path(root)
    name_pattern, fields = _compile_name_template(name_template)
    columns = fields + ["Mx", "My", "Mz", "M", "M_std"]
    rows: list[dict[str, float | int | str]] = []
    run_dirs = [
        entry
        for entry in root_path.iterdir()
        if entry.is_dir() and name_pattern.match(entry.name)
    ]

    for entry in run_dirs:
        match = name_pattern.match(entry.name)
        if match is None:
            continue
        try:
            variables = {
                key: _coerce_template_value(value)
                for key, value in match.groupdict().items()
            }
            averages = _read_averages_mean(
                entry,
                simid=simid,
                start=start,
                end=end,
                step=step,
            )
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


def collect_cumulants(
    root: str | Path,
    name_template: str,
    simid: str | None = None,
    start: int | None = None,
    end: int | None = None,
    step: int | None = None,
    strict: bool = True,
) -> pd.DataFrame:
    """
    Collect averaged cumulants columns from run directories matching a name template.

    Parameters:
        root: Directory containing run subdirectories.
        name_template: Folder name template with `{field}` placeholders used to
            extract variables into columns (e.g., "run_T{T}_P{P}").
        simid: Optional UppASD simid to select a specific output set within each
            run directory. When None, UppOut auto-detects the simid.
        start: Start index for row slicing (inclusive) before averaging.
        end: End index for row slicing (exclusive) before averaging.
        step: Step for row slicing before averaging.
        strict: When True, raise on any bad run; when False, skip with a warning.

    Returns:
        DataFrame containing one row per run directory. Columns include the
        extracted template variables and the averaged values for `M`, `M2`,
        `M4`, `Binder`, `chi`, `Cv`, `E`, `E_exch`, and `E_lsf`.
    """
    root_path = Path(root)
    name_pattern, fields = _compile_name_template(name_template)
    columns = fields + ["M", "M2", "M4", "Binder", "chi", "Cv", "E", "E_exch", "E_lsf"]
    rows: list[dict[str, float | int | str]] = []
    run_dirs = [
        entry
        for entry in root_path.iterdir()
        if entry.is_dir() and name_pattern.match(entry.name)
    ]

    for entry in run_dirs:
        match = name_pattern.match(entry.name)
        if match is None:
            continue
        try:
            variables = {
                key: _coerce_template_value(value)
                for key, value in match.groupdict().items()
            }
            cumulants = _read_cumulants_mean(
                entry,
                simid=simid,
                start=start,
                end=end,
                step=step,
            )
            row = {**variables, **cumulants}
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
