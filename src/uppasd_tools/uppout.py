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

    def _get_file_name(self, prefix: str) -> str:
        matches = self._prefix_to_files.get(prefix, [])
        if not matches:
            raise FileNotFoundError(
                f'No file starting with "{prefix}" found in "{self.dir_path}".'
            )
        return sorted(matches)[0]

    def _get_uppasd_output_file(self, prefix: str, simid: str) -> str:
        return f"{prefix}.{simid}.out"

    def _resolve_path(self, prefix: str, simid: str | None) -> Path:
        if simid and self.simid and simid != self.simid:
            raise ValueError(
                f'simid "{simid}" does not match detected simid "{self.simid}".'
            )
        resolved_simid = simid or self.simid
        if resolved_simid:
            path = self.dir_path / self._get_uppasd_output_file(prefix, resolved_simid)
        else:
            path = self.dir_path / self._get_file_name(prefix)
        if not path.is_file():
            raise FileNotFoundError(f'File not found: "{path}".')
        return path

    def read_averages(self, simid: str | None = None) -> pd.DataFrame:
        """
        Read an UppASD averages file into a pandas DataFrame.
        """

        path = self._resolve_path(self._prefix_averages, simid)
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

    def read_cumulants(self, simid: str | None = None) -> pd.DataFrame:
        """
        Read an UppASD cumulants file into a pandas DataFrame.
        """

        path = self._resolve_path(self._prefix_cumulants, simid)
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

    def read_coord(self, simid: str | None = None) -> pd.DataFrame:
        """
        Read an UppASD coord file into a pandas DataFrame.
        """

        path = self._resolve_path(self._prefix_coord, simid)
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

    def read_restart(self, simid: str | None = None) -> pd.DataFrame:
        """
        Read an UppASD restart file into a pandas DataFrame.
        """

        path = self._resolve_path(self._prefix_restart, simid)
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

    def read_struct(self, simid: str | None = None) -> pd.DataFrame:
        """
        Read an UppASD struct file into a pandas DataFrame.
        """

        path = self._resolve_path(self._prefix_struct, simid)
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

    def get_configs(self, simid: str | None = None) -> List[pd.DataFrame]:
        """ 
        Get configurations of all ensembles from a given simulation directory.
        Parameters:
            simid: Simulation identifier used in file names.
        Returns:
            List of pandas DataFrames, each containing the configuration for an ensemble.
        """

        df_coord = self.read_coord(simid)
        df_restart = self.read_restart(simid)

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
    
