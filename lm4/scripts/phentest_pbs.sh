#!/bin/bash
#PBS -N phentest
#PBS -q workq
#PBS -j oe
#PBS -V
#PBS -l select=1:ncpus=24:mpiprocs=24:host=climate01
# Run one phentest variant on a compute node (24 ranks, same layout as the climate00 runs).
#   qsub -v VARIANT=dayl2_d -N phentest_dayl2_d -o /data2/ydkoh/lm4/RUN/phentest_dayl2_d.pbs.log phentest_pbs.sh
# The variant must already be staged: VARIANTS="dayl2_d" bash phentest.sh setup 365
cd /data2/ydkoh/lm4/RUN || exit 1
echo "=== PBS job $PBS_JOBID on $(hostname), nodefile $(sort -u $PBS_NODEFILE | tr '\n' ' ') ($(wc -l < $PBS_NODEFILE) slots)"
HOSTFILE=$PBS_NODEFILE bash phentest.sh run "$VARIANT"
