##########################################################################################
# structure.py
#
# Functions for analyzing UppASD output data.
#
##########################################################################################

from .uppout import UppOut

import numpy as np
import pandas as pd

##########################################################################################

def get_neighbors(uppout: UppOut, at_num: int = 1) -> dict:
    """
    Get neighbors for a given atom number from the struct file.
    Parameters:
        uppout (UppOut): An instance of the UppOut class containing parsed output data.
        at_num (int): Atom number to get neighbors for.
    Returns:
        dict: A dictionary mapping neighbor atom numbers to dictionaries with
            keys: atom_type, position, Jexch.
    """
    df = uppout.read_struct()
    df = df[df["at1_num"] == at_num]
    if df.empty:
        raise ValueError(f'No neighbors found for atom number "{at_num}".')

    neighbors = {}
    for _, row in df.iterrows():
        pos = np.array([row["rx"], row["ry"], row["rz"]], dtype=float)
        atom_num = int(row["at2_num"])
        neighbors[atom_num] = {
            "atom_type": int(row["at2_type"]),
            "position": pos,
            "Jexch": float(row["Jexch"]),
        }
    return neighbors


def analyze_neighbors(
    uppout: UppOut,
    at_num: int = 1,
    dist_decimals: int | None = 3,
    jexch_decimals: int | None = 3,
    group_by: str = "distance",
) -> dict:
    """
    Analyze neighbor data for a given atom number from the structure DataFrame.
    Parameters:
        uppout (UppOut): An instance of the UppOut class containing parsed output data.
        at_num (int): Atom number to analyze neighbors for.
        dist_decimals (int | None): Decimal places used to bucket distances for grouping. Default is 3.
        jexch_decimals (int | None): Decimal places used to bucket Jexch for grouping. Default is 3.
        group_by (str): Grouping mode: "distance", "jexch", or "both".
    Returns:
        dict: A dictionary with atom types as keys and dictionaries with
            keys: distances, count, Jexch.
    """
    # Read structure data from UppOut instance
    df = uppout.read_struct()
    # Filter for the specified atom number
    df = df[df["at1_num"] == at_num].copy()
    if df.empty:
        raise ValueError(f'No neighbors found for atom number "{at_num}".')

    # Bucket float values to avoid tiny precision differences splitting groups.
    df["dist_key"] = df["dist"].round(dist_decimals) if dist_decimals is not None else df["dist"]
    df["Jexch_key"] = df["Jexch"].round(jexch_decimals) if jexch_decimals is not None else df["Jexch"]

    if group_by not in {"distance", "jexch", "both"}:
        raise ValueError('group_by must be "distance", "jexch", or "both".')

    group_cols = ["at2_type"]
    if group_by in {"distance", "both"}:
        group_cols.append("dist_key")
    if group_by in {"jexch", "both"}:
        group_cols.append("Jexch_key")

    # Group by atom type plus selected buckets, then count occurrences.
    # Keep the mean of original values for reporting.
    g = (
        df.groupby(group_cols, as_index=False)
          .agg(dist=("dist", "mean"), Jexch=("Jexch", "mean"), count=("dist", "size"))
    )

    # Create the output dictionary
    result = {
        k: {
            "distance": v["dist"].to_numpy(),
            "count": v["count"].to_numpy(),
            "Jexch": v["Jexch"].to_numpy(),
        }
        for k, v in g.groupby("at2_type")
    }

    return result
