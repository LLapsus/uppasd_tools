"""
Constants describing UppASD output file prefixes and column schemas.
"""

AVERAGES_PREFIX = "averages"
CUMULANTS_PREFIX = "cumulants"
COORD_PREFIX = "coord"
RESTART_PREFIX = "restart"
STRUCT_PREFIX = "struct"
ENERGY_PREFIX = "stdenergy"

AVERAGES_COLUMNS = ["iter", "Mx", "My", "Mz", "M", "M_stdv"]
CUMULANTS_COLUMNS = [
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
COORD_COLUMNS = ["at_num", "x", "y", "z", "at_type", "at_num_cell"]
RESTART_COLUMNS = ["ens_num", "at_num", "mom", "mx", "my", "mz"]
STRUCT_COLUMNS = [
    "at1_num",
    "at2_num",
    "at1_type",
    "at2_type",
    "rx",
    "ry",
    "rz",
    "Jexch",
    "dist",
]
ENERGY_COLUMNS = [
    "iter",
    "tot",
    "exch",
    "aniso",
    "DM",
    "PD",
    "BiqDM",
    "BQ",
    "dip",
    "Zeeman",
    "LSF",
    "chir",
    "ring",
    "sa",
]
