#!/bin/sh
#PBS -e rerun.err
#PBS -o rerun.log
#PBS -j oe
#PBS -V
#PBS -N lm4_rerun
#PBS -q workq
#PBS -l select=1:ncpus=24:mpiprocs=24:host=__HOST__

source /etc/profile.d/modules.sh
module purge
module load intel21/compiler-21
module load intel21/mkl
module load intel21/hdf5-1.10.5
module load intel21/netcdf-4.6.1
module load intel21/mvapich2-2.3.4

ulimit -s unlimited
export work_dir=__WORKDIR__
cd $work_dir

export MV2_SMP_USE_CMA=1
export MV2_IBA_EAGER_THRESHOLD=131072
export MV2_ENABLE_AFFINITY=0

NP=`cat $PBS_NODEFILE | wc -l`
echo "=== rerun launching on $NP ranks $(date) ==="
mpirun -hostfile $PBS_NODEFILE -np $NP ./fms_esm4.5_compile_v3_1007_fix.x > esm4p5.log 2>&1
echo "=== END rc=$? $(date) ==="
