#!/bin/bash
#PBS -N phentest_chain
#PBS -q workq
#PBS -l select=1:ncpus=24:mpiprocs=24:host=climate01
#PBS -j oe
# Run several already-staged phentest variants one after another on climate01 with the
# same 24-rank layout, so their wall-clock times are comparable (speed tests, LM4 notes 13.71).
#   qsub -v VARIANTS="ctrl1m ddep1m" -o /data2/ydkoh/lm4/RUN/phentest_chain.pbs.log phentest_pbs_chain.sh
cd /data2/ydkoh/lm4/RUN || exit 1
for v in $VARIANTS; do
  echo "##### $v  start $(date)  node load: $(cut -d' ' -f1-3 /proc/loadavg)"
  HOSTFILE=$PBS_NODEFILE bash ${PT:-phentest.sh} run "$v"
  awk '/Tabulating mpp_clock statistics/,0' phentest/$v/esm4p5.log > phentest/$v/clock_table.txt
  echo "##### $v  end   $(date)  restarts $(ls phentest/$v/RESTART | wc -l)  FATAL $(grep -a -c FATAL phentest/$v/esm4p5.log)"
done
