Quick start
===========

**Uppasd_tools** is designed to process UppASD simulation output. The output files of UppASD simulations are named as
`prefix.SIMID.out`, where `SIMID` is simulation id, 8-character string set in the UppASD main input file, `inpsd.dat`.

In ideal case, all results of your simulation are stored in one directory. 
To process these files, initialize UppOut object, which chacks the directory, finds available output files, 
and extracts available parameters.

.. code-block:: Python

    from uppasd_tools import UppOut

    uppout = UppOut('/path/to/UppASD/directory')

You can rewiev the information gathered by the uppout object.

.. code-block:: Python

    uppout.summary()

.. code-block:: text

    Output directory: ../data/bccFe
    Simulation ID: bcc_Fe_T
    Available output files: ['averages', 'coord', 'cumulants', 'mcinitial', 'restart', 'stdenergy', 'struct', 'totenergy']
    ---
    Number of atoms in the unit cell: 2
    Number of atom types: 1
    Total number of atoms in the supercell: 432
    Number of ensembles in the simulation: 5
    xrange: (0.0, 5.5)
    yrange: (0.0, 5.5)
    zrange: (0.0, 5.5)

It is important, that all the output files share the same `SIMID`, which means they were produced by the same simulation.
In case, you have stored outputs of multiple simulations in the same directory, UppOut will raise and error. 
You can correct it by specifying given `SIMID`.

.. code-block:: Python

    uppout = UppOut('/path/to/UppASD/directory', simid='bcc_Fe_T')
