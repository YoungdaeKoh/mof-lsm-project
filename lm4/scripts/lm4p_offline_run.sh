#!/bin/sh
### Route B step 1 probe: does the .not.do_atmos ("data atmos") path initialize
### and reach land_model_init / complete 1 coupling step (dt_cpld=3600)?
### Same 24-PE layout as the AMIP smoke test; total ranks MUST equal atmos_npes.
#PBS -e lm4_offline_probe.err
#PBS -o lm4_offline_probe.log
#PBS -j oe
#PBS -V
#PBS -N lm4_offline_probe
#PBS -q workq
#PBS -l select=1:ncpus=24:mpiprocs=24:host=climate01

source /etc/profile.d/modules.sh
module purge
module load intel21/compiler-21
module load intel21/mkl
module load intel21/hdf5-1.10.5
module load intel21/netcdf-4.6.1
module load intel21/mvapich2-2.3.4

ulimit -s unlimited

export work_dir=/data2/ydkoh/lm4/RUN/lm4_offline_probe
cd $work_dir

export MV2_SMP_USE_CMA=1
export MV2_IBA_EAGER_THRESHOLD=131072
# mvapich2-2.3.4 hydra treats binding as oversubscription -> disable affinity
export MV2_ENABLE_AFFINITY=0

NP=`cat $PBS_NODEFILE | wc -l`
echo "=== offline probe launching on $NP ranks (atmos_npes must=24) $(date) ==="
mpirun -hostfile $PBS_NODEFILE -np $NP ./fms_esm4.5_compile_v3_1007_fix.x > esm4p5.log 2>&1
echo "=== END rc=$? $(date) ==="
