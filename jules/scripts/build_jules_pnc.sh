#!/bin/bash
#====================================================================
# JULES vn7.4 rebuild against the PARALLEL netCDF/HDF5 stack
#   why: JULES passes an MPI communicator to file_ncdf_open
#        (internal_open_output_file.inc:130) unconditionally, so an MPI build
#        needs a netCDF with parallel support. The previous build pointed at
#        /usr/local/netcdf/4.6.1_intel21 (--has-parallel -> no), which failed at
#        the first output write with "Parallel operation on file opened for
#        non-parallel access".
#   MPI must be mvapich2 throughout: the *_mv234 netCDF/HDF5 were built with it,
#   and mixing it with oneAPI Intel MPI would break at runtime.
#====================================================================
set -e

MV=/usr/local/mpi/intel21/mvapich2-2.3.4
NC=/usr/local/netcdf/4.6.1_intel21_mv234
H5=/usr/local/hdf5/1.10.5_intel21_mv234

# put mvapich2 first so mpif90/mpicc resolve to it, not to oneAPI MPI
export PATH=$MV/bin:$HOME/fcm/bin:$PATH
export LD_LIBRARY_PATH=$MV/lib:$NC/lib:$H5/lib:$LD_LIBRARY_PATH

export JULES_COMPILER=intel
export JULES_BUILD=normal
export JULES_MPI=mpi
export JULES_OMP=noomp

export JULES_NETCDF=netcdf
export JULES_NETCDF_PATH=$NC
export JULES_NETCDF_INC_PATH=$NC/include
export JULES_NETCDF_LIB_PATH=$NC/lib

# libnetcdf in the mv234 tree is static only, so link it explicitly along with
# the parallel HDF5; otherwise libnetcdff.so resolves libnetcdf.so.13 back to
# the non-parallel /usr/local/netcdf/4.6.1_intel21 at run time.
export JULES_LDFLAGS_EXTRA="-L$NC/lib -lnetcdf -L$H5/lib -lhdf5_hl -lhdf5 -lz -lcurl"

echo "=== which mpif90: $(which mpif90) ==="
echo "=== netcdf parallel: $($NC/bin/nc-config --all | grep has-parallel) ==="

cd $HOME/jules-vn7.4
fcm make -j 4 -f etc/fcm-make/make.cfg
