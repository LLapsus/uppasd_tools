##########################################################################################
# analyze.py
#
# Functions for analysis of UppASD output data.
#
##########################################################################################

import numpy as np
import pandas as pd

from .uppout import UppOut

##########################################################################################

def _normalize_vectors(
    vectors: np.ndarray,
) -> np.ndarray:
    """
    Normalize vectors row-wise, returning zero vectors for zero norms.
    """
    norms = np.linalg.norm(vectors, axis=1)
    unit = np.zeros_like(vectors, dtype=float)
    nonzero = norms > 0
    unit[nonzero] = vectors[nonzero] / norms[nonzero][:, None]
    return unit

##########################################################################################

def sublattice_correlation_matrix(uppout: UppOut) -> np.ndarray:
    """
    Compute the correlation matrix between sublattice magnetization directions.

    Parameters:
        uppout: UppOut instance to read projavgs data from.

    Returns:
        NumPy array with shape (n_sublattices, n_sublattices). Each entry is
        the mean dot product between normalized magnetization vectors of two
        sublattices. Sublattices are ordered by sorted projection index.
    """
    # Read projavgs data and organize by sublattice index
    frames = uppout.read_projavgs()
    if not frames:
        raise ValueError("No projavgs data available.")

    # Extract and normalize magnetization vectors for each sublattice, indexed by sublattice index
    unit_by_proj: dict[int, pd.DataFrame] = {}
    for proj, frame in frames.items():
        if frame.empty:
            raise ValueError(f"No data rows found for proj {proj}.")
        vectors = frame[["Mx", "My", "Mz"]].to_numpy(dtype=float)  # magnetization vectors
        unit = _normalize_vectors(vectors)                         # normalized magnetization vectors
        iters = frame["iter"].to_numpy()                           # iteration numbers for alignment
        unit_by_proj[int(proj)] = pd.DataFrame(
            unit, index=iters, columns=["Mx", "My", "Mz"]
        )

    proj_ids = sorted(unit_by_proj)
    size = len(proj_ids)
    corr = np.empty((size, size), dtype=float)

    for i, proj_i in enumerate(proj_ids):
        ui = unit_by_proj[proj_i]
        for j, proj_j in enumerate(proj_ids):
            if j < i:
                corr[i, j] = corr[j, i]
                continue
            uj = unit_by_proj[proj_j]
            # Align on iteration numbers, keeping only iterations present in both sublattices
            aligned = ui.join(
                uj, how="inner", lsuffix="_i", rsuffix="_j"
            )
            if aligned.empty:
                raise ValueError(
                    "No overlapping iterations between proj "
                    f"{proj_i} and {proj_j}."
                )
            vi = aligned[["Mx_i", "My_i", "Mz_i"]].to_numpy()   # aligned magnetization vectors for sublattice i
            vj = aligned[["Mx_j", "My_j", "Mz_j"]].to_numpy()   # aligned magnetization vectors for sublattice j
            # Compute correlation
            corr_val = float(np.mean(np.sum(vi * vj, axis=1)))  # mean dot product
            corr[i, j] = corr_val
            corr[j, i] = corr_val

    return corr
