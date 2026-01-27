# UppASD Tools

**UppASD Tools** is a Python package for reading, validating, and post-processing output files
produced by atomistic spin dynamics or Monte Carlo simulations performed with
[UppASD](https://github.com/UppASD/UppASD) (Uppsala Atomistic Spin Dynamics).

The package focuses on robust parsing of common UppASD output formats as **pandas DataFrames**,
enabling direct use of the results with standard Python tools for data analysis and
visualization. This design choice simplifies aggregation of data across multiple
simulations and provides a natural foundation for future extensions towards
more advanced data analysis workflows.

UppASD Tools is intended to simplify exploratory analysis, regression testing of
simulation setups, and the development of reproducible post-processing workflows
in Python.

## Features

- Reading and parsing of common UppASD output files, including atomic positions,
  magnetic moments, neighbor structures, and simulation results
- Analysis of atomic pairs used to calculate exchange interactions
- Interactive 3D visualization of atomic structures and magnetic configurations
  using **py3Dmol**
- Collection and aggregation of data from multiple simulations to construct
  temperature-dependent observables, such as magnetization vs temperature
  or magnetic hysteresis


## Code structure

- `src/uppasd_tools/uppout.py`: Core `UppOut` reader. Scans a simulation output directory, detects the `simid`, and reads `*.out` files into pandas DataFrames.
- `src/uppasd_tools/uppout_schema.py`: File prefix and column schema definitions used by the readers.
- `src/uppasd_tools/collect.py`: Aggregation utilities for averaging results across multiple runs.
- `src/uppasd_tools/visualize.py`: 3D visualization helpers using **py3Dmol**.
- `src/uppasd_tools/structure.py`: Structure analysis helpers (e.g., neighbor lists).
- `src/uppasd_tools/__init__.py`: Public API exports.

## Installation

From the repository root:

```bash
pip install -e .
```

Or as a regular install:

```bash
pip install .
```

## Basic usage

```python
from uppasd_tools import UppOut

upp = UppOut("/path/to/simulation/output/directory")

# Access metadata
print(upp.simid)
print(upp.num_atoms, upp.num_atoms_cell, upp.num_atom_types, upp.num_ens)

# Read output files
df_avg     = upp.read_averages()
df_coord   = upp.read_coord()
df_restart = upp.read_restart()
df_struct  = upp.read_struct()
df_ener    = upp.read_energy()

# List of final configurations (per ensemble)
final_configs = upp.final_configs()

# Analyse structure
from uppasd_tools.structure import analyze_neighbors

neighbors = analyze_neighbors(upp, at_num=1)
```

Notes:
- Output files must follow the `prefix.simid.out` naming scheme and share a single `simid`.
- If multiple different `simid` values are detected, `UppOut` raises an error.
- You can pass `simid` to only index files with that identifier; it must be a string of exactly 8 characters.
- When `simid` is provided and no matching files exist, `UppOut` raises an error.

## Tests

From the repository root:

```bash
pytest
```

## Planned features

- Extended validation tools for exchange interactions and neighbour shells
- Additional visualization options for time-dependent data
- Implementing data alytical tools
