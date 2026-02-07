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

It is important, that all the output files share the same `SIMID`, which means they were produced by the same simulation.
In case, you have stored outputs of multiple simulations in the same directory, UppOut will raise and error. 
You can correct it by specifying given `SIMID`.

.. code-block:: Python

    uppout = UppOut('/path/to/UppASD/directory', simid='simid001')


Once you initialized `UppOut` object, you can rewiev the information gathered by the uppout object.

:fieldname: Summarize UppASD directory

.. code-block:: Python

    uppout.summary()

.. code-block:: text

    Output directory: /path/to/UppASD/directory
    Simulation ID: simid001
    Available output files: ['averages', 'coord', 'cumulants', 'mcinitial', 'restart', 'stdenergy', 'struct', 'totenergy']
    ---
    Number of atoms in the unit cell: 2
    Number of atom types: 1
    Total number of atoms in the supercell: 432
    Number of ensembles in the simulation: 5
    xrange: (0.0, 5.5)
    yrange: (0.0, 5.5)
    zrange: (0.0, 5.5)

Read UppASD output files
------------------------

UppOut holds simulation ID in `uppout.simid` and prefixes of all available output files in `uppout.prefixes`.
To read an output file you can use any of the function listed 
in :doc:`uppasd_tools.uppout reference <uppout>`.
For instance to read the `averages.simid001.out` file use

.. code-block:: Python

    df_averages = uppout.read_averages()

which returns a pandas dataframe containing the data from the file

+------+--------+--------+--------+--------+----------+
| iter | Mx     | My     | Mz     | M      | M_stdv   |
+======+========+========+========+========+==========+
| ...  | ...    | ...    | ...    | ...    | ...      |
+------+--------+--------+--------+--------+----------+

For more information see the 
`example Python notebook. <https://github.com/LLapsus/uppasd_tools/blob/78e493ae3d7236fcbab24c5b8ed11649b91f53fa/examples/read_output_files.ipynb>`_
