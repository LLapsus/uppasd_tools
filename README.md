# UppASD Tools

[UppASD](https://github.com/UppASD/UppASD) (Uppsala Atomistic Spin Dynamics) is a simulation suite to study magnetization dynamics by means of atomistic version of the Landau-Lifshitz-Gilbert (LLG) equation. Beside that it provides Monte Carlo methods to estimate equilibrium propertioes of magnetic materials.

**UppASD Tools** is a package for handling UppASD output files. I allows read, parse and process basic output files in a simple way in a Python code.

## Code structure

- `src/uppasd_tools/uppout.py`: Core `UppOut` reader. Scans a simulation output directory, detects the `simid`, and reads `*.out` files into pandas DataFrames.
- `src/uppasd_tools/analyze.py`: Analysis helpers built on top of `UppOut` data (e.g., neighbor statistics).
- `src/uppasd_tools/__init__.py`: Public API exports.

## Basic usage

```python
from uppasd_tools import UppOut
from uppasd_tools.analyze import analyze_neighbours

upp = UppOut("/path/to/simulation/output/directory")

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
