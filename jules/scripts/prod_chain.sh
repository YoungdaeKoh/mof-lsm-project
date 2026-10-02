#!/bin/bash
# JULES vn7.4 1-deg production run: WFDE5 1979-2023, TRIFFID dynamic mode.
#
# Differences from spin-up A (spinup_A_chain.sh): l_trif_eq=.false. and
# triffid_period=5 (dynamic mode; 5 divides the 365-day year, so no TRIFFID
# accumulation is lost when each yearly run restarts: the accumulators and
# asteps_since_triffid are not dump variables), data_start 1979, data_end one
# record past 2024-01-01 (wfde5_1deg_2024.nc is a lookahead-only copy).
# Unchanged: nn-filled WFDE5, l_leap=.false., l_veg_compete=.false., 24 ranks.
#
# IC for 1979 = end of spin-up cycle 3 (2011-01-01 dump; a dump with a
# different date is accepted, tested in test_dumpic).  Other years = dump at
# the end of the previous year.  Every year is gated; a stopped chain resumes.
# Nothing is deleted.
# usage (climate00, from the run dir):
#   nohup bash prod_chain.sh >& chain.log < /dev/null &

R=/home/ydkoh/JULES_runs/prod_1979_2023
OUT=/data2/ydkoh/JULES_runs/prod_1979_2023/output
SPIN_IC=/data2/ydkoh/JULES_runs/spinup_A_trifeq/output/jules_spinA_c03.dump.20110101.0.nc
GATE=/home/ydkoh/JULES_runs/chk_jules_year.py
EXE=/home/ydkoh/jules-vn7.4/build/bin/jules.exe
RID=jules_prod
NP=${NP:-24}
Y0=${Y0:-1979}
Y1=${Y1:-2023}

MV=/usr/local/mpi/intel21/mvapich2-2.3.4
NC=/usr/local/netcdf/4.6.1_intel21_mv234
H5=/usr/local/hdf5/1.10.5_intel21_mv234
IFRT=/usr/local/intel/oneapi/compiler/2022.0.1/linux/compiler/lib/intel64_lin
export PATH=$MV/bin:$PATH
export LD_LIBRARY_PATH=$MV/lib:$NC/lib:$H5/lib:$IFRT:/usr/local/zlib/1.2.11/lib:$LD_LIBRARY_PATH
export MV2_ENABLE_AFFINITY=0

source /home/ydkoh/anaconda3/etc/profile.d/conda.sh
conda activate

cd $R || exit 1
mkdir -p $OUT logs
sed "s/^ *run_id *=.*/  run_id = '$RID',/; s|^ *output_dir *=.*|  output_dir = '$OUT'|" \
    output.nml.tmpl > output.nml

write_timesteps() {   # $1 = year
  cat > timesteps.nml <<EOF
&JULES_TIME
! WFDE5 forcing is 365_day (1460 records every year), so no leap days here.
  l_leap         = .false.,
  timestep_len   = 1800,

  main_run_start = '$1-01-01 00:00:00',
  main_run_end   = '$(($1 + 1))-01-01 00:00:00'
/

&JULES_SPINUP
  max_spinup_cycles = 0
/
EOF
}

write_ic() {          # $1 = dump file
  cat > initial_conditions.nml <<EOF
&JULES_INITIAL
! All prognostics from the previous dump (nvars=0 -> every required variable).
  dump_file = .true.,
  file      = '$1',
/
EOF
}

echo "=== production $Y0-$Y1, np=$NP, START $(date) ==="
for y in $(seq $Y0 $Y1); do
  end_dump=$OUT/$RID.dump.$((y + 1))0101.0.nc
  if [ -s $end_dump ] && python $GATE $OUT $RID $y > /dev/null 2>&1; then
    echo "  $y already done"; continue
  fi
  if [ $y -eq 1979 ]; then ic=$SPIN_IC; else ic=$OUT/$RID.dump.${y}0101.0.nc; fi
  if [ ! -s $ic ]; then echo "STOP $y: IC $ic missing"; exit 1; fi
  write_timesteps $y
  write_ic $ic
  log=logs/${RID}_$y.log
  t0=$(date +%s)
  mpirun -np $NP $EXE > $log 2>&1
  rc=$?
  if [ $rc -ne 0 ] || grep -q FATAL $log || [ ! -s $end_dump ]; then
    echo "STOP $y: rc=$rc, FATAL=$(grep -c FATAL $log), end dump $( [ -s $end_dump ] && echo ok || echo missing) -> $log"
    exit 1
  fi
  if ! python $GATE $OUT $RID $y; then
    echo "STOP $y: gate failed"; exit 1
  fi
  echo "  $y done in $(( $(date +%s) - t0 )) s ($(date +%H:%M)), IC=$(basename $ic)"
done
echo "=== END $(date) ==="
