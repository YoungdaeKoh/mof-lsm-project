#!/bin/bash
# JULES 1 deg smoke test: one month (Jan 1981), GSWP3 1 deg, TRIFFID on, cold start.
#
# The runtime library path MUST put the *_mv234 (parallel) netCDF/HDF5 and
# mvapich2 first: the sonames (libnetcdf.so.13, libmpi.so.12) also exist in the
# non-parallel / oneAPI-MPI trees and whichever comes first wins (notes, MPI
# section, trap 1).
cd ~/JULES_runs/prod_1deg_test
MV=/usr/local/mpi/intel21/mvapich2-2.3.4
NC=/usr/local/netcdf/4.6.1_intel21_mv234
H5=/usr/local/hdf5/1.10.5_intel21_mv234
# The mv234 netCDF/HDF5 were built with Intel, so the exe needs the ifort runtime
# (libifport.so.5).  The login node has it through the oneAPI environment; a PBS
# job launched from a non-interactive shell does not, and the exe dies with
# "error while loading shared libraries" before a single time step.
IFRT=/usr/local/intel/oneapi/compiler/2022.0.1/linux/compiler/lib/intel64_lin
export PATH=$MV/bin:$PATH
export LD_LIBRARY_PATH=$MV/lib:$NC/lib:$H5/lib:$IFRT:/usr/local/zlib/1.2.11/lib:$LD_LIBRARY_PATH
export MV2_ENABLE_AFFINITY=0
NP=${NP:-8}
echo "=== start $(date), np=$NP ==="
grep -h "nx =\|ny =" model_grid.nml
grep -h "file =" drive.nml
ldd ~/jules-vn7.4/build/bin/jules.exe | grep -E "netcdf|libmpi\.so"
time mpirun -np $NP ~/jules-vn7.4/build/bin/jules.exe
echo "=== end rc=$? $(date) ==="
ls -lh output/
