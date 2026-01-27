# UppASD Tools

**UppASD Tools** is a Python package for reading, validating, and post-processing output files
produced by atomistic spin dynamics or Monte Carlo simulations performed with
[UppASD](https://github.com/UppASD/UppASD) (Uppsala Atomistic Spin Dynamics).

The package focuses on robust parsing of common UppASD output formats and on
consistency checks of simulation results (atomic positions, magnetic moments,
site/type mappings, and interaction data), which are often a source of subtle errors
in custom analysis scripts.

UppASD Tools is intended to simplify exploratory analysis, regression testing of
simulation setups, and the development of reproducible post-processing workflows
in Python.

## Features

- Reading and parsing of common UppASD output files (atomic positions, magnetic moments,
  and related simulation data)
- Consistency checks of simulation outputs (site/type mapping, duplicated atoms or bonds,
  numerical tolerances, and basic sanity checks)
- Interactive 3D visualization of atomic structures and magnetic configurations
  using **py3Dmol**
- Collection and aggregation of data from multiple simulations to construct
  temperature-dependent observables (e.g. magnetization vs temperature)
- Support for analysing field-dependent simulations, enabling construction of
  hysteresis curves and related quantities


## Code structure

- `src/uppasd_tools/uppout.py`: Core `UppOut` reader. Scans a simulation output directory, detects the `simid`, and reads `*.out` files into pandas DataFrames.
- `src/uppasd_tools/analyze.py`: Analysis helpers built on top of `UppOut` data (e.g., neighbor statistics).
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
from uppasd_tools.analyze import analyze_neighbours

upp = UppOut("/path/to/simulation/output/directory")
# Or target a specific simid (8-character string, spaces allowed)
upp = UppOut("/path/to/simulation/output/directory", simid="00000001")

# Read output files
df_avg = upp.read_averages()
df_coord = upp.read_coord()
df_struct = upp.read_struct()

# Access metadata
print(upp.simid)
print(upp.num_atoms, upp.num_atoms_cell, upp.num_atom_types, upp.num_ens)

# Analyse structure
neighbors = analyze_neighbours(upp, at_num=1)
```

Notes:
- Output files must follow the `prefix.simid.out` naming scheme and share a single `simid`.
- If multiple different `simid` values are detected, `UppOut` raises an error.
- You can pass `simid` to only index files with that identifier; it must be a string of exactly 8 characters.
- When `simid` is provided and no matching files exist, `UppOut` raises an error.
