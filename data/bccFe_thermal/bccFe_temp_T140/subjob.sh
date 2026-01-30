#!/bin/bash
#
# script submits simulated annealing of bcc Fe
#
###############################################################################

#PBS -N bcc_Fe
#PBS -l select=1:ncpus=16:mem=4gb:scratch_local=16gb
#PBS -l walltime=1:00:00
#PBS -q luna
#PBS -j oe

# set number of threads
export OMP_NUM_THREADS=$PBS_NUM_PPN

# settings and file name
Jfile="jfile*"        # jfile name
Posfile="posfile*"    # posfile name
Momfile="momfile*"    # momfile name

# set the working directory
DATADIR="$PBS_O_WORKDIR"

# additional info files
JOB_INFO=$DATADIR/info.out
STD_OUT=$DATADIR/uppasd.out

# setting the automatical cleaning of the SCRATCH
trap 'clean_scratch' TERM EXIT

# set number of processors
module load intelcdk
module load intel-mkl
module load openmpi

# change directory
cd $SCRATCHDIR

# input data copy
cp $DATADIR/inpsd.dat $SCRATCHDIR
cp $DATADIR/$Jfile $SCRATCHDIR
cp $DATADIR/$Posfile $SCRATCHDIR
cp $DATADIR/$Momfile $SCRATCHDIR

# run simulation
# /storage/praha1/home/balaz/local/UppASD-master-ifort/source/sd
/storage/praha1/home/balaz/local/UppASD6/UppASD-6.1/source/sd

# copy results to my Datadir
cp ./*.out $DATADIR 

# clear output files
rm ./*.out

