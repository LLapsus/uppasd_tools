# UppASD Tools

**UppASD Tools** is intended for researchers using the [UppASD](https://github.com/UppASD/UppASD)
package to streamline post-processing and analysis of simulation outputs.

The package focuses on robust parsing of common UppASD output formats into pandas DataFrames,
enabling direct use of the results with standard Python tools for data analysis and visualization.

The goal of UppASD Tools is to simplify exploratory analysis, regression testing of simulation setups,
and the development of reproducible post-processing workflows in Python.

## Features

- Reading and parsing of common UppASD output files, including atomic positions,
  magnetic moments, neighbor structures, and simulation results
- Analysis of atomic pairs used for the calculation of exchange interactions
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
print(upp.summary())

# Read output files as pandas DataFrames
df_avg     = upp.read_averages()    # read averages.simid.out
df_cumu    = upp.read_cumulants()   # read cumulants.simid.out
df_coord   = upp.read_coord()       # read coord.simid.out
df_restart = upp.read_restart()     # read restart.simid.out
df_struct  = upp.read_struct()      # read struct.simid.out
df_ener    = upp.read_energy()      # read totenergy.simid.out and stdenergy.simid.out

# List of final configurations (per ensemble)
final_configs = upp.final_configs()

# Analyse structure
from uppasd_tools.structure import analyze_neighbors

neighbors = analyze_neighbors(upp, at_num=1)

# 3D interactive visualizations
from uppasd_tools.visualize import visualize_supercell, visualize_final_config

visualize_supercell(upp)                   # visualize atomic structure   
visualoze_final_config(upp, ens_index=2)   # visualize magnetic configuration

# Collect data from different simulations to plot eg. temperature dependence
from uppasd_tools.collect import collect_averages

df_temp = collect_averages(
  "/path/to/data/directory", name_template="SimResults_T{T}", simid="simid001"
)
```

## Dependencies

Basic runtime dependencies (installed with the package):

- pandas
- numpy
- py3Dmol

Optional extras:

- `viz`: playwright (PNG rendering)
- `notebooks`: jupyterlab, matplotlib, ipywidgets
- `dev`: pytest

## Tests

From the repository root:

```bash
pytest
```

## Examples

- [examples/read_output_files.ipynb](examples/read_output_files.ipynb): Use UppOut object to inspect simulation metadata and read output files as pandas DataFrames.
- [examples/visualize_structure.ipynb](examples/visualize_structure.ipynb): Visualize atomic structures and magnetic configurations using py3Dmol.
- [examples/analyze_structure.ipynb](examples/analyze_structure.ipynb): Analyze neighbor shells and exchange interactions from the struct file.
- [examples/collect_data.ipynb](examples/collect_data.ipynb): Collect and aggregate outputs across different simulations to obtain temperature dependence of desired quantities.

## Planned features

- Extended validation tools for exchange interactions and neighbour shells
- Additional visualization options for time-dependent data
- Implementing data alytical tools
