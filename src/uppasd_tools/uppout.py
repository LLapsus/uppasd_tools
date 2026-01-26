##########################################################################################
# uppout.py
#
# Class UppOut for reading and parsing UppASD output files.
#
##########################################################################################

import logging
from typing import List, SupportsInt, cast

import pandas as pd
from pathlib import Path

from .uppout_schema import (
    AVERAGES_COLUMNS,
    AVERAGES_PREFIX,
    COORD_COLUMNS,
    COORD_PREFIX,
    CUMULANTS_COLUMNS,
    CUMULANTS_PREFIX,
    ENERGY_COLUMNS,
    ENERGY_PREFIX,
    PROJCUMULANTS_COLUMNS,
    PROJCUMULANTS_PREFIX,
    PROJAVGS_COLUMNS,
    PROJAVGS_PREFIX,
    RESTART_COLUMNS,
    RESTART_PREFIX,
    STRUCT_COLUMNS,
    STRUCT_PREFIX,
)

##########################################################################################

# Set up logging
logger = logging.getLogger(__name__)

class UppOut:
    """
    Reader for UppASD output files within a simulation directory.
    """

    # Prefixes for different UppASD output files
    _prefix_averages = AVERAGES_PREFIX
    _prefix_cumulants = CUMULANTS_PREFIX
    _prefix_coord = COORD_PREFIX
    _prefix_energy = ENERGY_PREFIX
    _prefix_projcumulants = PROJCUMULANTS_PREFIX
    _prefix_projavgs = PROJAVGS_PREFIX
    _prefix_restart = RESTART_PREFIX
    _prefix_struct = STRUCT_PREFIX

    def __init__(self, dir_path: str | Path, simid: str | None = None) -> None:
        # Set up directory path
        self.dir_path = Path(dir_path)
        if not self.dir_path.is_dir():
            raise NotADirectoryError(f'Directory not found: "{self.dir_path}".')

        self.simid = None
        if simid is not None:
            self._validate_simid(simid)
            self.simid = simid

        # List all files in the directory
        if self.simid is None:
            self.file_names = sorted(
                entry.name for entry in self.dir_path.iterdir() if entry.is_file()
            )
        else:
            self.file_names = sorted(
                entry.name
                for entry in self.dir_path.iterdir()
                if entry.is_file() and self._matches_simid(entry.name, self.simid)
            )
            if not self.file_names:
                raise FileNotFoundError(
                    f'No output files found for simid "{self.simid}" in '
                    f'"{self.dir_path}".'
                )
        self._prefix_to_files: dict[str, List[str]] = {}
        self._prefix_to_simids: dict[str, List[str]] = {}
        self._index_output_files()
        
        # Determine prefixes and simid
        self.prefixes = sorted(self._prefix_to_files.keys())
        if self.simid is None:
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
                    f"{', '.join(simids)}\n Please specify a simid to use."
                )
            self.simid = simids[0] if simids else None
        
        # Load counts of atoms, atom types, and ensembles
        self.num_atoms = None       # Total number of atoms in the simulation
        self.num_atoms_cell = None  # Number of atoms in the unit cell
        self.num_atom_types = None  # Number of unique atom types
        self.num_ens = None         # Number of ensembles in the simulation
        self.xrange = None          # (min, max) x-coordinates from coord file
        self.yrange = None          # (min, max) y-coordinates from coord file
        self.zrange = None          # (min, max) z-coordinates from coord file
        self._load_counts()

    def _load_counts(self) -> None:
        coord_name = None
        restart_name = None
        if self.simid:
            coord_name = f"{self._prefix_coord}.{self.simid}.out"
            restart_name = f"{self._prefix_restart}.{self.simid}.out"

        # Load number of atoms and atom types from coord file
        if coord_name and coord_name in self.file_names:
            df_coord = self.read_coord()
            self.num_atoms = len(df_coord)
            self.num_atoms_cell = len(df_coord["at_num_cell"].unique())
            self.num_atom_types = len(df_coord["at_type"].unique())
            self.xrange = (float(df_coord["x"].min()), float(df_coord["x"].max()))
            self.yrange = (float(df_coord["y"].min()), float(df_coord["y"].max()))
            self.zrange = (float(df_coord["z"].min()), float(df_coord["z"].max()))

        # Load number of ensembles from restart file
        if restart_name and restart_name in self.file_names:
            df_restart = self.read_restart()
            self.num_ens = len(df_restart["ens_num"].unique())

    def _index_output_files(self) -> None:
        for name in self.file_names:
            parts = name.split(".")
            if len(parts) != 3 or parts[2] != "out":
                continue
            prefix, simid = parts[0], parts[1]
            if self.simid is not None and simid != self.simid:
                continue
            self._prefix_to_files.setdefault(prefix, []).append(name)
            self._prefix_to_simids.setdefault(prefix, []).append(simid)

    @staticmethod
    def _validate_simid(simid: str) -> None:
        if not isinstance(simid, str):
            raise TypeError("simid must be a string with 8 characters.")
        if len(simid) != 8:
            raise ValueError("simid must be a string with 8 characters.")

    @staticmethod
    def _matches_simid(name: str, simid: str) -> bool:
        parts = name.split(".")
        return len(parts) == 3 and parts[1] == simid and parts[2] == "out"

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
                header=None,
                skiprows=1,
                skip_blank_lines=True,
            )
            frame.columns = AVERAGES_COLUMNS
            return frame
        except Exception as exc:
            logger.error("Failed to read averages file %s: %s", path, exc)
            raise

    def read_projavgs(self) -> dict[int, pd.DataFrame]:
        """
        Read an UppASD projavgs file into a dict of DataFrames keyed by projection index.
        """

        path = self._resolve_path(self._prefix_projavgs)
        try:
            frame = pd.read_csv(
                path,
                sep=r"\s+",
                engine="python",
                header=None,
                comment="#",
                skip_blank_lines=True,
            )
            if frame.shape[1] != len(PROJAVGS_COLUMNS):
                raise ValueError(
                    "Unexpected column count in projavgs file: "
                    f"{frame.shape[1]} (expected {len(PROJAVGS_COLUMNS)})."
                )
            frame.columns = PROJAVGS_COLUMNS
            frames: dict[int, pd.DataFrame] = {}
            for proj, group in frame.groupby("proj"):
                proj_key = int(cast(SupportsInt, proj))
                frames[proj_key] = group.reset_index(drop=True)
            return frames
        except Exception as exc:
            logger.error("Failed to read projavgs file %s: %s", path, exc)
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
            frame.columns = CUMULANTS_COLUMNS
            return frame
        except Exception as exc:
            logger.error("Failed to read cumulants file %s: %s", path, exc)
            raise

    def read_projcumulants(self) -> dict[int, pd.DataFrame]:
        """
        Read an UppASD projcumulants file into a dict of DataFrames keyed by projection index.
        """

        path = self._resolve_path(self._prefix_projcumulants)
        try:
            frame = pd.read_csv(
                path,
                sep=r"\s+",
                engine="python",
                header=None,
                comment="#",
                skip_blank_lines=True,
            )
            if frame.shape[1] != len(PROJCUMULANTS_COLUMNS):
                raise ValueError(
                    "Unexpected column count in projcumulants file: "
                    f"{frame.shape[1]} (expected {len(PROJCUMULANTS_COLUMNS)})."
                )
            frame.columns = PROJCUMULANTS_COLUMNS
            frames: dict[int, pd.DataFrame] = {}
            for proj, group in frame.groupby("proj"):
                proj_key = int(cast(SupportsInt, proj))
                frames[proj_key] = group.reset_index(drop=True)
            return frames
        except Exception as exc:
            logger.error("Failed to read projcumulants file %s: %s", path, exc)
            raise

    def read_energy(self) -> pd.DataFrame:
        """
        Read an UppASD stdenergy file into a pandas DataFrame.
        """

        path = self._resolve_path(self._prefix_energy)
        try:
            frame = pd.read_csv(
                path,
                sep=r"\s+",
                engine="python",
                header=0,
                skip_blank_lines=True,
            )
            frame.columns = ENERGY_COLUMNS
            return frame
        except Exception as exc:
            logger.error("Failed to read stdenergy file %s: %s", path, exc)
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
            frame.columns = COORD_COLUMNS
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
            frame.columns = RESTART_COLUMNS
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
            frame.columns = STRUCT_COLUMNS
            return frame
        except Exception as exc:
            logger.error("Failed to read struct file %s: %s", path, exc)
            raise

    def final_configs(self) -> List[pd.DataFrame]:
        """ 
        Get final configurations of all ensembles from a restart file.
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

    def atom_type(self, at_num: int) -> int:
        """
        Return the atom type for a given atom number using the coord data.
        """

        df_coord = self.read_coord()
        match = df_coord.loc[df_coord["at_num"] == at_num, "at_type"]
        if match.empty:
            raise ValueError(f'Atom number "{at_num}" not found in coord data.')
        return int(match.iloc[0])
    
