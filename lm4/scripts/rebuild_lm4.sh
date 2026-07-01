#!/bin/bash
# Incremental rebuild after sphum.F90 qscomp clamp patch.
set -e
export SPACK_STACK_DIR=/data2/ydkoh/spack-stack
source /data2/ydkoh/spack-stack/spack/share/spack/setup-env.sh
spack load /evn6nxf
cd /data2/ydkoh/lm4/ufs-weather-model/build
echo "=== make start $(date) ==="
OMP_NUM_THREADS=1 make -j 4
echo "=== make DONE exit=$? $(date) ==="
ls -l ufs_model
