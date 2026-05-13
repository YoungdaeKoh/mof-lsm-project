#!/bin/tcsh -f
cd ~/CESM/cime/scripts

set CCSMROOT = /home/ydkoh/CESM
set CNAME = f2000_clm5_test
set COMPSET = F2000Nuopc
set RES = f19_g17

# Clean previous case and output
rm -rf $CCSMROOT/cases/$CNAME
rm -rf /data2/ydkoh/cesm2_output/$CNAME

# Create new case
./create_newcase --case $CCSMROOT/cases/$CNAME \
                 --compset $COMPSET \
                 --res $RES \
                 --machine climate00 \
                 --compiler intel \
                 --mpilib mvapich2 \
                 --run-unsupported

cd $CCSMROOT/cases/$CNAME

# Setup case
./case.setup

# Task configuration (48 cores for all components)
./xmlchange NTASKS=48
./xmlchange ROOTPE_ATM=0,ROOTPE_LND=0,ROOTPE_ROF=0
./xmlchange NTASKS_ATM=48,NTASKS_LND=48,NTASKS_ROF=48
./xmlchange NTASKS_ICE=48,NTASKS_OCN=48,NTASKS_GLC=48
./xmlchange NTASKS_WAV=48,NTASKS_CPL=48

# Build and submit
./case.build
./case.submit
