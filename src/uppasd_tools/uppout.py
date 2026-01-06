##########################################################################################
# uppout.py
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

class UppOut:
    """
    Reader for UppASD output files within a simulation directory.
    """

    # Prefixes for different UppASD output files
    _prefix_averages = "averages"
    _prefix_cumulants = "cumulants"
    _prefix_coord = "coord"
    _prefix_restart = "restart"
    _prefix_struct = "struct"

    def __init__(self, dir_path: str | Path) -> None:
        self.dir_path = Path(dir_path)
        if not self.dir_path.is_dir():
            raise NotADirectoryError(f'Directory not found: "{self.dir_path}".')

        self.file_names = sorted(
            entry.name for entry in self.dir_path.iterdir() if entry.is_file()
        )
        self._prefix_to_files: dict[str, List[str]] = {}
        self._prefix_to_simids: dict[str, List[str]] = {}
        self._index_output_files()
        self.prefixes = sorted(self._prefix_to_files.keys())
        simids = sorted(
            {
                simid
                for simids in self._prefix_to_simids.values()
                for simid in simids
            }
        )
        if len(simids) > 1:
            raise ValueError(
                "Multiple simid values detected in output files: "
                f"{', '.join(simids)}"
            )
        self.simid = simids[0] if simids else None

    def _index_output_files(self) -> None:
        for name in self.file_names:
            parts = name.split(".")
            if len(parts) != 3 or parts[2] != "out":
                continue
            prefix, simid = parts[0], parts[1]
            self._prefix_to_files.setdefault(prefix, []).append(name)
            self._prefix_to_simids.setdefault(prefix, []).append(simid)

    def _get_uppasd_output_file(self, prefix: str) -> str:
        if not self.simid:
            raise ValueError("No simid detected in output files.")
        return f"{prefix}.{self.simid}.out"

    def _resolve_path(self, prefix: str) -> Path:
        file_name = self._get_uppasd_output_file(prefix)
        if file_name not in self.file_names:
            raise FileNotFoundError(
                f'File not found in "{self.dir_path}": "{file_name}".'
            )
        path = self.dir_path / file_name
        if not path.is_file():
            raise FileNotFoundError(f'File not found: "{path}".')
        return path

    def read_averages(self) -> pd.DataFrame:
        """
        Read an UppASD averages file into a pandas DataFrame.
        """

        path = self._resolve_path(self._prefix_averages)
        try:
            frame = pd.read_csv(
                path,
                sep=r"\s+",
                engine="python",
                header=0,
                skip_blank_lines=True,
            )
            frame.columns = ["iter", "Mx", "My", "Mz", "M", "M_stdv"]
            return frame
        except Exception as exc:
            logger.error("Failed to read averages file %s: %s", path, exc)
            raise

    def read_cumulants(self) -> pd.DataFrame:
        """
        Read an UppASD cumulants file into a pandas DataFrame.
        """

        path = self._resolve_path(self._prefix_cumulants)
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

    def read_coord(self) -> pd.DataFrame:
        """
        Read an UppASD coord file into a pandas DataFrame.
        """

        path = self._resolve_path(self._prefix_coord)
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

    def read_restart(self) -> pd.DataFrame:
        """
        Read an UppASD restart file into a pandas DataFrame.
        """

        path = self._resolve_path(self._prefix_restart)
        try:
            frame = pd.read_csv(
                path,
                sep=r"\s+",
                engine="python",
                header=None,
                skip_blank_lines=True,
                comment="#",
            )
            frame = frame.iloc[:, 1:]
            frame.columns = ["ens_num", "at_num", "mom", "mx", "my", "mz"]
            return frame
        except Exception as exc:
            logger.error("Failed to read restart file %s: %s", path, exc)
            raise

    def read_struct(self) -> pd.DataFrame:
        """
        Read an UppASD struct file into a pandas DataFrame.
        """

        path = self._resolve_path(self._prefix_struct)
        try:
            frame = pd.read_csv(
                path,
                sep=r"\s+",
                engine="python",
                header=None,
                skip_blank_lines=True,
                comment="#",
            )
            frame.columns = [
                "at1_num",
                "at2_num",
                "at1_type",
                "at2_type",
                "rx",
                "ry",
                "rz",
                "jexch",
                "dist",
            ]
            return frame
        except Exception as exc:
            logger.error("Failed to read struct file %s: %s", path, exc)
            raise

    def get_configs(self) -> List[pd.DataFrame]:
        """ 
        Get configurations of all ensembles from a given simulation directory.
        Parameters:
        Returns:
            List of pandas DataFrames, each containing the configuration for an ensemble.
        """

        df_coord = self.read_coord()
        df_restart = self.read_restart()

        configs: List[pd.DataFrame] = []
        ensables = df_restart["ens_num"].unique()

        for ens in ensables:
            df_ens = df_restart[df_restart["ens_num"] == ens].copy()
            df_ens.reset_index(drop=True, inplace=True)
            df_ens = df_ens.merge(
                df_coord,
                left_on="at_num",
                right_on="at_num",
                how="left",
                suffixes=("_restart", "_coord"),
            )
            df_ens.drop(columns=["ens_num"], inplace=True, errors="ignore")
            configs.append(df_ens)

        return configs
    
