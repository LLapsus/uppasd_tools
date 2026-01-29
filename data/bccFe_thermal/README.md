# Temperature dependence of BCC Fe

This folder contains number of Monte Carlo simulations of BCC Fe at various temperatures ranging from 20 to 1600 K with temperature step 20K.
Input and output files for each simulation are stored in a separate folder. The input files originate from [UppASD test directory](https://github.com/UppASD/UppASD/tree/d8d666328afedcd588c1f610d958fa259d964a82/tests/bccFe).

The simulations have been run using the bash script `submit_all.sh`.

## Monte Carlo simulations

Each simulation consists of
- initial phase: thermalization (3000 MC steps at temperature T)
- main phase: 2000 MC steps at temperature T