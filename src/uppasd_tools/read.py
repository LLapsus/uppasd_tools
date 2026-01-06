##########################################################################################
# read_out.py
#
# Functions to read and parse output files from the uppasd simulation runs.
#
##########################################################################################

import logging
from typing import List

import pandas as pd
from pathlib import Path

##########################################################################################

# Set up logging
logger = logging.getLogger(__name__)

# --- UppASD Output File Prefixes ---

_prefix_averages  = "averages"
_prefix_cumulants = "cumulants"
_prefix_coord     = "coord"
_prefix_restart   = "restart"

# --- Helper Functions ---

def _get_file_name(prefix: str, dir_path: str | Path) -> str:
    """
    Find a file in dir_path whose name starts with given prefix.
    """
    
    # Ensure the directory exists
    path = Path(dir_path)
    if not path.is_dir():
        raise NotADirectoryError(f'Directory not found: "{path}".')

    matches = sorted(entry.name for entry in path.iterdir() if entry.name.startswith(prefix))
    if not matches:
        raise FileNotFoundError(f'No file starting with "{prefix}" found in "{path}".')
    return matches[0]

def _get_uppasd_output_file(_prefix: str, simid: str) -> str:
    """
    Construct the UppASD output file name based on prefix and simid.
    """
    return f"{_prefix}.{simid}.out"

# --- Functions to read and parse UppASD output files ---

def read_averages(dir_path: str | Path, simid: str | None = None) -> pd.DataFrame:
    """
    Read an UppASD averages file into a pandas DataFrame.
    """
    
    # Ensure the directory exists
    base_path = Path(dir_path)
    if not base_path.is_dir():
        raise NotADirectoryError(f'Directory not found: "{base_path}".')

    # Resolve file path
    if simid:
        path = base_path / _get_uppasd_output_file(_prefix_averages, simid)
    else:
        path = base_path / _get_file_name(_prefix_averages, base_path)

    # Ensure the file exists
    if not path.is_file():
        raise FileNotFoundError(f'Averages file not found: "{path}".')

    # Read the file using pandas
    try:
        frame = pd.read_csv(
            path,
            sep=r"\s+",
            engine="python",
            header=0,
            skip_blank_lines=True,
        )
        frame.columns = [
            "iter", 
            "Mx", 
            "My", 
            "Mz", 
            "M", 
            "M_stdv"
        ]
        return frame
    except Exception as exc:
        logger.error("Failed to read averages file %s: %s", path, exc)
        raise


def read_cumulants(dir_path: str | Path, simid: str | None = None) -> pd.DataFrame:
    """
    Read an UppASD cumulants file into a pandas DataFrame.
    """
    
    # Ensure the directory exists
    base_path = Path(dir_path)
    if not base_path.is_dir():
        raise NotADirectoryError(f'Directory not found: "{base_path}".')

    # Resolve file path
    if simid:
        path = base_path / _get_uppasd_output_file(_prefix_cumulants, simid)
    else:
        path = base_path / _get_file_name(_prefix_cumulants, base_path)

    # Ensure the file exists
    if not path.is_file():
        raise FileNotFoundError(f'Cumulants file not found: "{path}".')

    # Read the file using pandas
    try:
        frame = pd.read_csv(
            path,
            sep=r"\s+",
            engine="python",
            header=0,
            skip_blank_lines=True,
        )
        frame.columns = [
            "iter",
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
        return frame
    except Exception as exc:
        logger.error("Failed to read cumulants file %s: %s", path, exc)
        raise


def read_coord(dir_path: str | Path, simid: str | None = None) -> pd.DataFrame:
    """
    Read an UppASD coord file into a pandas DataFrame.
    """

    # Ensure the directory exists
    base_path = Path(dir_path)
    if not base_path.is_dir():
        raise NotADirectoryError(f'Directory not found: "{base_path}".')

    # Resolve file path
    if simid:
        path = base_path / _get_uppasd_output_file(_prefix_coord, simid)
    else:
        path = base_path / _get_file_name(_prefix_coord, base_path)

    # Ensure the file exists
    if not path.is_file():
        raise FileNotFoundError(f'Coord file not found: "{path}".')

    # Read the file using pandas
    try:
        frame = pd.read_csv(
            path,
            sep=r"\s+",
            engine="python",
            header=None,
            skip_blank_lines=True,
        )
        frame.columns = [
            "at_num",
            "x",
            "y",
            "z",
            "at_type",
            "at_num_cell",
        ]
        return frame
    except Exception as exc:
        logger.error("Failed to read coord file %s: %s", path, exc)
        raise


def read_restart(dir_path: str | Path, simid: str | None = None) -> pd.DataFrame:
    """
    Read an UppASD restart file into a pandas DataFrame.
    """

    # Ensure the directory exists
    base_path = Path(dir_path)
    if not base_path.is_dir():
        raise NotADirectoryError(f'Directory not found: "{base_path}".')

    # Resolve file path
    if simid:
        path = base_path / _get_uppasd_output_file(_prefix_restart, simid)
    else:
        path = base_path / _get_file_name(_prefix_restart, base_path)

    # Ensure the file exists
    if not path.is_file():
        raise FileNotFoundError(f'Restart file not found: "{path}".')

    # Read the file using pandas
    try:
        frame = pd.read_csv(
            path,
            sep=r"\s+",
            engine="python",
            header=None,
            skip_blank_lines=True,
            skiprows=7,
        )
        frame = frame.iloc[:, 1:]
        frame.columns = ["ens_num", "at_num", "mom", "mx", "my", "mz"]
        return frame
    except Exception as exc:
        logger.error("Failed to read restart file %s: %s", path, exc)
        raise

# --- Function to get configurations of all ensembles ---

def get_configs(dir_path: str | Path, simid: str | None = None) -> List[pd.DataFrame]:
    """ 
    Get configurations of all ensembles from a given simulation directory.
    Parameters:
        dir_path: Path to the simulation directory.
        simid: Simulation identifier used in file names.
    Returns:
        List of pandas DataFrames, each containing the configuration for an ensemble.
    """
    
    # Ensure the directory exists
    path = Path(dir_path)
    if not path.is_dir():
        raise NotADirectoryError(f'Directory not found: "{path}".')
    
    # Read coord and restart files
    df_coord   = read_coord(path, simid)
    df_restart = read_restart(path, simid)
    
    configs: List[pd.DataFrame] = []           # List to hold configurations of all ensembles
    ensables = df_restart['ens_num'].unique()  # Get unique ensemble numbers
    
    # Process each ensemble
    for ens in ensables:
        df_ens = df_restart[df_restart['ens_num'] == ens].copy()
        df_ens.reset_index(drop=True, inplace=True)
        df_ens = df_ens.merge(
            df_coord,
            left_on='at_num',
            right_on='at_num',
            how='left',
            suffixes=('_restart', '_coord')
        )
        df_ens.drop(columns=["ens_num"], inplace=True, errors="ignore")
        configs.append(df_ens)
        
    return configs
    
