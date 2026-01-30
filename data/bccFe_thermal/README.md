# Temperature dependence of BCC Fe

This folder contains number of Monte Carlo simulations of BCC Fe at various temperatures ranging from 20 to 1600 K with temperature step 20K.
Input and output files for each simulation are stored in a separate folder. The input files originate from [UppASD test directory](https://github.com/UppASD/UppASD/tree/d8d666328afedcd588c1f610d958fa259d964a82/tests/bccFe).

The simulations have been run using the bash script `submit_all.sh`.

Some of the UppASD output files were removed in order to reduce the size of the data directory.

## Monte Carlo simulations

We simulated 3D superlattice of size: 10 x 10 x 10 with periodic boundary conditions.

Each simulation consists of
- initial phase: thermalization (10^5 MC steps at temperature T)
- main phase: 4 x 10^4 MC steps at temperature T