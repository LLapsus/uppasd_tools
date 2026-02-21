##########################################################################################
# collect.py
#
# Functions to collect averaged UppASD output data from multiple simulation runs.
# Can be used to aggregate data from parameter sweeps into a single DataFrame.
# Examples: temperature dependces, magnetic field scans, hysteresis loops, etc.
#
##########################################################################################

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

import pandas as pd

from .uppout import UppOut
from .uppout_schema import (
    AVERAGES_COLUMNS,
    CUMULANTS_COLUMNS,
    ENERGY_COLUMNS,
    PROJCUMULANTS_COLUMNS,
    PROJAVGS_COLUMNS,
)

try:
    from tqdm.auto import tqdm
except ImportError:  # pragma: no cover - optional dependency
    tqdm = None

##########################################################################################

logger = logging.getLogger(__name__)

# Template regex patterns
TEMPLATE_FIELD_RE = re.compile(r"{([A-Za-z_][A-Za-z0-9_]*)}")
INT_RE = re.compile(r"^-?\d+$")
FLOAT_RE = re.compile(r"^-?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][+-]?\d+)?$")

##########################################################################################

def _ensure_root_dir(root: str | Path) -> Path:
    """Validate and return the root directory used for run discovery."""
    root_path = Path(root)
    if not root_path.exists():
        msg = f'Root path "{root_path}" does not exist.'
        logger.error(msg)
        raise FileNotFoundError(msg)
    if not root_path.is_dir():
        msg = f'Root path "{root_path}" is not a directory.'
        logger.error(msg)
        raise NotADirectoryError(msg)
    return root_path


def _find_run_dirs(
    root_path: Path,
    name_pattern: re.Pattern[str],
    name_template: str,
) -> list[Path]:
    """Return run subdirectories whose names match the compiled template."""
    run_dirs = [
        entry
        for entry in root_path.iterdir()
        if entry.is_dir() and name_pattern.match(entry.name)
    ]
    if not run_dirs:
        msg = (
            f'No subdirectories in "{root_path}" match template "{name_template}".'
        )
        logger.error(msg)
        raise ValueError(msg)
    return run_dirs


def _log_missing_output(entry: Path, exc: FileNotFoundError) -> None:
    """Emit a consistent error message for missing run output files."""
    logger.error("Missing output file for run %s: %s", entry, exc)


def _compile_name_template(template: str) -> tuple[re.Pattern[str], list[str]]:
    """
    Convert a folder template into a regex and ordered placeholder names.

    Example:
        "run_T{T}_P{P}" -> pattern with named groups "T" and "P".
    """
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
    """Cast extracted template values to int/float when possible."""
    if INT_RE.match(value):
        return int(value)
    if FLOAT_RE.match(value):
        return float(value)
    return value


def _iter_with_progress(iterable, enabled: bool, desc: str | None = None):
    """Wrap an iterable with tqdm or a simple stderr progress indicator."""
    if enabled and tqdm is not None:
        return tqdm(iterable, desc=desc)
    if enabled:
        return _simple_progress(iterable, desc=desc)
    return iterable


def _simple_progress(iterable, desc: str | None = None):
    """Fallback progress printer used when tqdm is unavailable."""
    total = len(iterable) if hasattr(iterable, "__len__") else None
    label = desc or "progress"

    def _gen():
        """Yield items while printing current iteration count to stderr."""
        count = 0
        for item in iterable:
            count += 1
            if total is None:
                msg = f"{label}: {count}"
            else:
                msg = f"{label}: {count}/{total}"
            print(f"\r{msg}", end="", file=sys.stderr)
            yield item
        print(file=sys.stderr)

    return _gen()


def _read_averages_mean(
    run_dir: str | Path,
    simid: str | None = None,
    start: int | None = None,
    end: int | None = None,
    step: int | None = None,
) -> dict[str, float]:
    """Read `averages.*.out` and return sliced mean values for scalar columns."""
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
    mean_columns = [column for column in AVERAGES_COLUMNS if column != "iter"]
    output_columns = [
        "M_std" if column == "M_stdv" else column for column in mean_columns
    ]
    mean_row = slice_rows[mean_columns].mean()
    return {
        output: float(mean_row[column])
        for column, output in zip(mean_columns, output_columns)
    }


def _read_projavgs_mean(
    run_dir: str | Path,
    simid: str | None = None,
    start: int | None = None,
    end: int | None = None,
    step: int | None = None,
) -> dict[int, dict[str, float]]:
    """Read `projavgs.*.out` and return per-projection sliced means."""
    run_path = Path(run_dir)
    uppout = UppOut(run_path, simid=simid) if simid else UppOut(run_path)
    frames = uppout.read_projavgs()
    if not frames:
        raise ValueError(
            f'No data rows found in projavgs file for "{run_path}".'
        )
    mean_columns = [
        column
        for column in PROJAVGS_COLUMNS
        if column not in ("iter", "proj")
    ]
    output_columns = [
        "M_std" if column == "M_stdv" else column for column in mean_columns
    ]
    output: dict[int, dict[str, float]] = {}
    for proj, frame in frames.items():
        if frame.empty:
            raise ValueError(
                f'No data rows found in projavgs file for "{run_path}" '
                f'(proj {proj}).'
            )
        slice_rows = frame.iloc[slice(start, end, step)]
        if slice_rows.empty:
            raise ValueError(
                f'No data rows found in selected range for "{run_path}" '
                f'(proj {proj}).'
            )
        mean_row = slice_rows[mean_columns].mean()
        output[proj] = {
            out_name: float(mean_row[col_name])
            for col_name, out_name in zip(mean_columns, output_columns)
        }
    return output


def _read_projcumulants_mean(
    run_dir: str | Path,
    simid: str | None = None,
    start: int | None = None,
    end: int | None = None,
    step: int | None = None,
) -> dict[int, dict[str, float]]:
    """Read `projcumulants.*.out` and return per-projection sliced means."""
    run_path = Path(run_dir)
    uppout = UppOut(run_path, simid=simid) if simid else UppOut(run_path)
    frames = uppout.read_projcumulants()
    if not frames:
        raise ValueError(
            f'No data rows found in projcumulants file for "{run_path}".'
        )
    mean_columns = [
        column
        for column in PROJCUMULANTS_COLUMNS
        if column not in ("iter", "proj")
    ]
    output: dict[int, dict[str, float]] = {}
    for proj, frame in frames.items():
        if frame.empty:
            raise ValueError(
                f'No data rows found in projcumulants file for "{run_path}" '
                f'(proj {proj}).'
            )
        slice_rows = frame.iloc[slice(start, end, step)]
        if slice_rows.empty:
            raise ValueError(
                f'No data rows found in selected range for "{run_path}" '
                f'(proj {proj}).'
            )
        mean_row = slice_rows[mean_columns].mean()
        output[proj] = {
            column: float(mean_row[column]) for column in mean_columns
        }
    return output


def _read_cumulants_mean(
    run_dir: str | Path,
    simid: str | None = None,
    start: int | None = None,
    end: int | None = None,
    step: int | None = None,
) -> dict[str, float]:
    """Read `cumulants.*.out` and return sliced mean values."""
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
    mean_columns = [column for column in CUMULANTS_COLUMNS if column != "iter"]
    mean_row = slice_rows[mean_columns].mean()
    return {column: float(mean_row[column]) for column in mean_columns}


def _read_energy_mean(
    run_dir: str | Path,
    simid: str | None = None,
    start: int | None = None,
    end: int | None = None,
    step: int | None = None,
) -> dict[str, float]:
    """Read `stdenergy.*.out` and return sliced mean values."""
    run_path = Path(run_dir)
    uppout = UppOut(run_path, simid=simid) if simid else UppOut(run_path)
    frame = uppout.read_energy()
    if frame.empty:
        raise ValueError(
            f'No data rows found in stdenergy file for "{run_path}".'
        )
    slice_rows = frame.iloc[slice(start, end, step)]
    if slice_rows.empty:
        raise ValueError(
            f'No data rows found in selected range for "{run_path}".'
        )
    mean_columns = [column for column in ENERGY_COLUMNS if column != "iter"]
    mean_row = slice_rows[mean_columns].mean()
    return {column: float(mean_row[column]) for column in mean_columns}

##########################################################################################

def get_matching_directories(
    root: str | Path,
    name_template: str,
    *,
    sort: bool = True,
) -> dict[
    str,
    list[Path] | list[float | int | str],
]:
    """
    Return run subdirectories matching a folder-name template.

    Parameters:
        root: Directory containing run subdirectories.
        name_template: Folder name template with `{field}` placeholders used for
            matching (e.g., "run_T{T}_P{P}").
        sort: When True, return paths sorted by directory name.

    Returns:
        Dictionary with:
        - `directories`: list of matching run directory paths.
        - one key per placeholder field: list of values in directory order.
    """
    root_path = _ensure_root_dir(root)
    name_pattern, fields = _compile_name_template(name_template)
    if "directories" in fields:
        raise ValueError(
            'Template placeholder "directories" is reserved by the '
            "get_matching_directories output schema."
        )
    run_dirs = _find_run_dirs(root_path, name_pattern, name_template)
    matched: list[tuple[Path, dict[str, float | int | str]]] = []
    for run_dir in run_dirs:
        match = name_pattern.match(run_dir.name)
        if match is None:
            continue
        group_values = match.groupdict()
        values_by_field = {
            field: _coerce_template_value(group_values[field]) for field in fields
        }
        matched.append((run_dir, values_by_field))

    if sort:
        matched.sort(key=lambda item: item[0].name)

    directories: list[Path] = []
    field_values: dict[str, list[float | int | str]] = {
        field: [] for field in fields
    }

    for run_dir, values_by_field in matched:
        directories.append(run_dir)
        for field in fields:
            field_values[field].append(values_by_field[field])

    output: dict[
        str,
        list[Path] | list[float | int | str],
    ] = {"directories": directories}
    output.update(field_values)
    return output


def collect_averages(
    root: str | Path,
    name_template: str,
    simid: str | None = None,
    start: int | None = None,
    end: int | None = None,
    step: int | None = None,
    strict: bool = True,
    progress: bool = True,
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
            Missing output files are always skipped with an error log.
        progress: When True, show a progress bar during collection.

    Returns:
        DataFrame containing one row per run directory. Columns include the
        extracted template variables and the averaged values for
        `Mx`, `My`, `Mz`, `M`, and `M_std`.
    """
    root_path = _ensure_root_dir(root)
    name_pattern, fields = _compile_name_template(name_template)
    mean_columns = [column for column in AVERAGES_COLUMNS if column != "iter"]
    output_columns = [
        "M_std" if column == "M_stdv" else column for column in mean_columns
    ]
    columns = fields + output_columns
    rows: list[dict[str, float | int | str]] = []
    run_dirs = _find_run_dirs(root_path, name_pattern, name_template)

    for entry in _iter_with_progress(run_dirs, progress, desc="collect_averages"):
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
        except FileNotFoundError as exc:
            _log_missing_output(entry, exc)
            continue
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


def collect_projavgs(
    root: str | Path,
    name_template: str,
    simid: str | None = None,
    start: int | None = None,
    end: int | None = None,
    step: int | None = None,
    strict: bool = True,
    progress: bool = True,
) -> dict[int, pd.DataFrame]:
    """
    Collect averaged projavgs columns from run directories matching a name template.

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
            Missing output files are always skipped with an error log.
        progress: When True, show a progress bar during collection.

    Returns:
        Dictionary of DataFrames, one per projection index. Columns include the
        extracted template variables and the averaged values for
        `M`, `M_std`, `Mx`, `My`, and `Mz`.
    """
    root_path = _ensure_root_dir(root)
    name_pattern, fields = _compile_name_template(name_template)
    mean_columns = [
        column
        for column in PROJAVGS_COLUMNS
        if column not in ("iter", "proj")
    ]
    output_columns = [
        "M_std" if column == "M_stdv" else column for column in mean_columns
    ]
    columns = fields + output_columns
    rows_by_proj: dict[int, list[dict[str, float | int | str]]] = {}
    run_dirs = _find_run_dirs(root_path, name_pattern, name_template)

    for entry in _iter_with_progress(run_dirs, progress, desc="collect_projavgs"):
        match = name_pattern.match(entry.name)
        if match is None:
            continue
        try:
            variables = {
                key: _coerce_template_value(value)
                for key, value in match.groupdict().items()
            }
            proj_means = _read_projavgs_mean(
                entry,
                simid=simid,
                start=start,
                end=end,
                step=step,
            )
            for proj, averages in proj_means.items():
                row = {**variables, **averages}
                rows_by_proj.setdefault(proj, []).append(row)
        except FileNotFoundError as exc:
            _log_missing_output(entry, exc)
            continue
        except Exception as exc:
            if strict:
                raise
            logger.warning("Skipping run %s: %s", entry, exc)

    if not rows_by_proj:
        return {}

    frames: dict[int, pd.DataFrame] = {}
    for proj, rows in rows_by_proj.items():
        if not rows:
            frames[proj] = pd.DataFrame(columns=columns)
            continue
        frame = pd.DataFrame(rows, columns=columns)
        frame.sort_values(fields, inplace=True)
        frame.reset_index(drop=True, inplace=True)
        frames[proj] = frame

    return frames


def collect_projcumulants(
    root: str | Path,
    name_template: str,
    simid: str | None = None,
    start: int | None = None,
    end: int | None = None,
    step: int | None = None,
    strict: bool = True,
    progress: bool = True,
) -> dict[int, pd.DataFrame]:
    """
    Collect averaged projcumulants columns from run directories matching a name template.

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
            Missing output files are always skipped with an error log.
        progress: When True, show a progress bar during collection.

    Returns:
        Dictionary of DataFrames, one per projection index. Columns include the
        extracted template variables and the averaged values for
        `M`, `M2`, `M4`, `Binder`, and `chi`.
    """
    root_path = _ensure_root_dir(root)
    name_pattern, fields = _compile_name_template(name_template)
    mean_columns = [
        column
        for column in PROJCUMULANTS_COLUMNS
        if column not in ("iter", "proj")
    ]
    columns = fields + mean_columns
    rows_by_proj: dict[int, list[dict[str, float | int | str]]] = {}
    run_dirs = _find_run_dirs(root_path, name_pattern, name_template)

    for entry in _iter_with_progress(run_dirs, progress, desc="collect_projcumulants"):
        match = name_pattern.match(entry.name)
        if match is None:
            continue
        try:
            variables = {
                key: _coerce_template_value(value)
                for key, value in match.groupdict().items()
            }
            proj_means = _read_projcumulants_mean(
                entry,
                simid=simid,
                start=start,
                end=end,
                step=step,
            )
            for proj, averages in proj_means.items():
                row = {**variables, **averages}
                rows_by_proj.setdefault(proj, []).append(row)
        except FileNotFoundError as exc:
            _log_missing_output(entry, exc)
            continue
        except Exception as exc:
            if strict:
                raise
            logger.warning("Skipping run %s: %s", entry, exc)

    if not rows_by_proj:
        return {}

    frames: dict[int, pd.DataFrame] = {}
    for proj, rows in rows_by_proj.items():
        if not rows:
            frames[proj] = pd.DataFrame(columns=columns)
            continue
        frame = pd.DataFrame(rows, columns=columns)
        frame.sort_values(fields, inplace=True)
        frame.reset_index(drop=True, inplace=True)
        frames[proj] = frame

    return frames


def collect_cumulants(
    root: str | Path,
    name_template: str,
    simid: str | None = None,
    start: int | None = None,
    end: int | None = None,
    step: int | None = None,
    strict: bool = True,
    progress: bool = True,
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
            Missing output files are always skipped with an error log.
        progress: When True, show a progress bar during collection.

    Returns:
        DataFrame containing one row per run directory. Columns include the
        extracted template variables and the averaged values for
        `M`, `M2`, `M4`, `Binder`, `chi`, `Cv`, `E`, `E_exch`, and `E_lsf`.
    """
    root_path = _ensure_root_dir(root)
    name_pattern, fields = _compile_name_template(name_template)
    mean_columns = [column for column in CUMULANTS_COLUMNS if column != "iter"]
    columns = fields + mean_columns
    rows: list[dict[str, float | int | str]] = []
    run_dirs = _find_run_dirs(root_path, name_pattern, name_template)

    for entry in _iter_with_progress(run_dirs, progress, desc="collect_cumulants"):
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
        except FileNotFoundError as exc:
            _log_missing_output(entry, exc)
            continue
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


def collect_energies(
    root: str | Path,
    name_template: str,
    simid: str | None = None,
    start: int | None = None,
    end: int | None = None,
    step: int | None = None,
    strict: bool = True,
    progress: bool = True,
) -> pd.DataFrame:
    """
    Collect averaged energy columns from run directories matching a name template.

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
            Missing output files are always skipped with an error log.
        progress: When True, show a progress bar during collection.

    Returns:
        DataFrame containing one row per run directory. Columns include the
        extracted template variables and the averaged values for
        `tot`, `exch`, `aniso`, `DM`, `PD`, `BiqDM`, `BQ`, `dip`, `Zeeman`, `LSF`, and `chir`.
    """
    root_path = _ensure_root_dir(root)
    name_pattern, fields = _compile_name_template(name_template)
    mean_columns = [column for column in ENERGY_COLUMNS if column != "iter"]
    columns = fields + mean_columns
    rows: list[dict[str, float | int | str]] = []
    run_dirs = _find_run_dirs(root_path, name_pattern, name_template)

    for entry in _iter_with_progress(run_dirs, progress, desc="collect_energies"):
        match = name_pattern.match(entry.name)
        if match is None:
            continue
        try:
            variables = {
                key: _coerce_template_value(value)
                for key, value in match.groupdict().items()
            }
            energies = _read_energy_mean(
                entry,
                simid=simid,
                start=start,
                end=end,
                step=step,
            )
            row = {**variables, **energies}
            rows.append(row)
        except FileNotFoundError as exc:
            _log_missing_output(entry, exc)
            continue
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
