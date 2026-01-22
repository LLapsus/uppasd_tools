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
        dict: A dictionary mapping neighbor atom numbers to [atom_type, position, Jexch].
    """
    df = uppout.read_struct()
    df = df[df["at1_num"] == at_num]
    if df.empty:
        raise ValueError(f'No neighbors found for atom number "{at_num}".')

    neighbors = {}
    for _, row in df.iterrows():
        pos = np.array([row["rx"], row["ry"], row["rz"]], dtype=float)
        neighbors[int(row["at2_num"])] = [int(row["at2_type"]), pos, float(row["Jexch"])]
    return neighbors


def analyze_neighbors(
    uppout: UppOut,
    at_num: int = 1,
    dist_decimals: int | None = 3,
    jexch_decimals: int | None = 3,
) -> dict:
    """
    Analyze neighbor data for a given atom number from the structure DataFrame.
    Parameters:
        uppout (UppOut): An instance of the UppOut class containing parsed output data.
        at_num (int): Atom number to analyze neighbors for.
        dist_decimals (int | None): Decimal places used to bucket distances for grouping. Default is 3.
        jexch_decimals (int | None): Decimal places used to bucket Jexch for grouping. Default is 3.
    Returns:
        dict: A dictionary with atom types as keys and tuples of (distances, counts, Jexch) as values.
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

    # Group by atom type, bucketed distance, and bucketed exchange, then count occurrences.
    # Keep the mean of original values for reporting.
    g = (
        df.groupby(["at2_type", "dist_key", "Jexch_key"], as_index=False)
          .agg(dist=("dist", "mean"), Jexch=("Jexch", "mean"), count=("dist", "size"))
    )

    # Create the output dictionary
    result = {
        k: (
            v["dist"].to_numpy(),
            v["count"].to_numpy(),
            v["Jexch"].to_numpy(),
        )
        for k, v in g.groupby("at2_type")
    }

    return result
