#!/bin/sh
### One model year of lm4p_ctl_1979-2024 at 48 PE.
### 48 ranks with npes_io_group=48: the io group has to span the whole PE set,
### otherwise the land's unstructured grid is written as .0001/.0002 pieces and
### the chain's archive pattern silently drops half of every diagnostic
### (LM4_SPINUP_NOTES 13.48).
#PBS -e lm4p_ctl.err
#PBS -o lm4p_ctl.log
#PBS -j oe
#PBS -V
#PBS -N lm4p_ctl
#PBS -q workq
#PBS -l select=1:ncpus=48:mpiprocs=48:host=climate01

source /etc/profile.d/modules.sh
module purge
module load intel21/compiler-21
module load intel21/mkl
module load intel21/hdf5-1.10.5
module load intel21/netcdf-4.6.1
module load intel21/mvapich2-2.3.4

ulimit -s unlimited

export work_dir=/data2/ydkoh/lm4/RUN/lm4p_ctl_1979-2024
cd $work_dir

export MV2_SMP_USE_CMA=1
export MV2_IBA_EAGER_THRESHOLD=131072
# mvapich2-2.3.4 hydra treats binding as oversubscription -> disable affinity
export MV2_ENABLE_AFFINITY=0

NP=`cat $PBS_NODEFILE | wc -l`
echo "=== lm4p_ctl launching on $NP ranks (atmos_npes must=48) $(date) ==="
# stdout to a file, never to the PBS stream: an undelivered PBS stdout is what
# filled climate01's root filesystem and stalled every job for four days (13.49)
mpirun -hostfile $PBS_NODEFILE -np $NP ./fms_esm4.5_compile_v3_1007_fix.x > esm4p5.log 2>&1
echo "=== END rc=$? $(date) ==="
