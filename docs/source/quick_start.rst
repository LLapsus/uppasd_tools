Quick start
===========

**Uppasd_tools** is designed to process UppASD simulation output. The output files of UppASD simulations are named as
`prefix.SIMID.out`, where `SIMID` is simulation id, 8-character string set in the UppASD main input file, `inpsd.dat`.

In ideal case, all results of your simulation are stored in one directory. 
To process these files, initialize UppOut object, which chacks the directory, finds available output files, 
and extracts available parameters.

.. code-block:: Python

    from pathlib import Path
    from uppasd_tools import UppOut

    path = Path('/path/to/UppASD/directory')

    uppout = UppOut(path)


