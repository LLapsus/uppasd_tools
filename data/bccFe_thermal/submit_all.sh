#!/bin/bash
#
# submit all jobs
#
###############################################################################

# range of temperatures
Tlower="10"   # lower temperature
Tupper="1600"   # upper temperature
Tstep="20"    # temperature step

# Job name
JobName="bccFe_temp"
SimID="bccFe_T_"

# generate list of temperature
TempList=`echo "for(temp=$Tupper;temp>$Tlower-.5*$Tstep;temp-=$Tstep) {temp;}" | bc`

# run simulations for all temperatures
for Temp in $TempList
do
  # Copy the Base directory
  Dir=$JobName"_T"$Temp
  mkdir -p ./$Dir
  cp ./Base/* $Dir

  # change directory
  cd $Dir

  #set job name
  sed -i "s/SIMID/$SimID/g" ./inpsd.dat

  # set temperature
  sed -i "s/TEMP/$Temp/g" ./inpsd.dat

  # set seed for random number generator
  Seed=$RANDOM
  sed -i "s/SEED/$Seed/g" ./inpsd.dat

  # submit simulation
  qsub subjob.sh
  echo "Temperature "$Temp" submitted"

  # change director
  cd ..
 
done

