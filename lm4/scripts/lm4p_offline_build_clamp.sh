#!/bin/bash
# Rebuild the clone with the qscomp clamp in lm4P/shared/sphum.F90.
# Only the clone is touched; ~/ESM4p5_KIOSTv2b stays as built.
set -e

export BASEDIR=/data2/ydkoh/lm4/esm4p5-lm4p-offline

source /etc/profile.d/modules.sh
module purge
module load intel21/compiler-21
module load intel21/mkl
module load intel21/hdf5-1.10.5
module load intel21/netcdf-4.6.1
module load intel21/mvapich2-2.3.4
ulimit -s unlimited

cd "$BASEDIR/exec"

echo "=== confirming the clamp is in the source the build will read ==="
grep -n 'Tc = min' "$BASEDIR/src/lm4P/shared/sphum.F90"

echo "=== rebuilding liblm4P.a ==="
make BASEDIR="$BASEDIR" SRCROOT="$BASEDIR/src/" BUILDROOT="$BASEDIR/exec/" \
     MK_TEMPLATE="$BASEDIR/exec/intel_tomo.mk" lm4P/liblm4P.a

echo "=== relinking executable ==="
make BASEDIR="$BASEDIR" SRCROOT="$BASEDIR/src/" BUILDROOT="$BASEDIR/exec/" \
     MK_TEMPLATE="$BASEDIR/exec/intel_tomo.mk" fms_esm4.5_compile_v3_1007_fix.x

echo "=== result ==="
ls -la "$BASEDIR/exec/fms_esm4.5_compile_v3_1007_fix.x"
