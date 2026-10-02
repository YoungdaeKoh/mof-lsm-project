#!/bin/bash
# JULES vn7.4 1-deg spin-up A: WFDE5 1981-2010 cycling, TRIFFID equilibrium mode.
#
# Settings (notes 13-15): forcing = nearest-neighbour filled WFDE5 1 deg,
# l_leap=.false. (forcing is 365_day), triffid_period=365 with l_trif_eq=.true.
# (one equilibrium update per model year), l_veg_compete=.false. (tile
# fractions fixed to the ancil), 24 MPI ranks (48 is 4x slower, notes 15).
#
# One JULES run per model year, so every year is gated before the next starts
# and a stopped chain resumes from the last good year.  IC for each year:
#   cycle 1, 1981 : cold start (initial_conditions.cold.nml, constants)
#   cycle N, 1981 : dump of cycle N-1 at 2011-01-01
#   other years   : dump written at the end of the previous year
# Since triffid_period equals the run length, the equilibrium update fires at
# the last step of each yearly run, as in the 2-year test (test_trif365).
#
# Nothing is deleted (raw preservation).  Output goes to /data2.
# usage (climate00, from the run dir):
#   nohup bash spinup_A_chain.sh <first_cycle> <last_cycle> >& chain.log < /dev/null &

R=/home/ydkoh/JULES_runs/spinup_A_trifeq
OUT=/data2/ydkoh/JULES_runs/spinup_A_trifeq/output
GATE=/home/ydkoh/JULES_runs/chk_jules_year.py
EXE=/home/ydkoh/jules-vn7.4/build/bin/jules.exe
NP=${NP:-24}
C0=${1:-1}
C1=${2:-1}
Y0=1981
Y1=2010

# Runtime environment: same as run_1deg_test.sh (mv234 parallel netCDF first,
# ifort runtime for the Intel-built netCDF/HDF5).
MV=/usr/local/mpi/intel21/mvapich2-2.3.4
NC=/usr/local/netcdf/4.6.1_intel21_mv234
H5=/usr/local/hdf5/1.10.5_intel21_mv234
IFRT=/usr/local/intel/oneapi/compiler/2022.0.1/linux/compiler/lib/intel64_lin
export PATH=$MV/bin:$PATH
export LD_LIBRARY_PATH=$MV/lib:$NC/lib:$H5/lib:$IFRT:/usr/local/zlib/1.2.11/lib:$LD_LIBRARY_PATH
export MV2_ENABLE_AFFINITY=0

# python for the gate (anaconda on the server)
source /home/ydkoh/anaconda3/etc/profile.d/conda.sh
conda activate

cd $R || exit 1
mkdir -p $OUT logs
# keep the cold-start IC and the output template before the chain rewrites them
[ -s initial_conditions.cold.nml ] || cp -p initial_conditions.nml initial_conditions.cold.nml
[ -s output.nml.tmpl ] || cp -p output.nml output.nml.tmpl

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

write_ic() {          # $1 = dump file, or "cold"
  if [ "$1" = cold ]; then
    cp -p initial_conditions.cold.nml initial_conditions.nml
  else
    cat > initial_conditions.nml <<EOF
&JULES_INITIAL
! All prognostics from the previous dump (nvars=0 -> every required variable).
  dump_file = .true.,
  file      = '$1',
/
EOF
  fi
}

echo "=== spin-up A chain: cycles $C0-$C1, years $Y0-$Y1, np=$NP, START $(date) ==="
for c in $(seq $C0 $C1); do
  rid=$(printf 'jules_spinA_c%02d' $c)
  sed "s/^ *run_id *=.*/  run_id = '$rid',/; s|^ *output_dir *=.*|  output_dir = '$OUT'|" \
      output.nml.tmpl > output.nml
  for y in $(seq $Y0 $Y1); do
    end_dump=$OUT/$rid.dump.$((y + 1))0101.0.nc
    # resume: a year whose end dump exists and whose output passes the gate is done
    if [ -s $end_dump ] && python $GATE $OUT $rid $y > /dev/null 2>&1; then
      echo "  c$c $y already done"; continue
    fi
    if [ $c -eq 1 ] && [ $y -eq $Y0 ]; then
      ic=cold
    elif [ $y -eq $Y0 ]; then
      ic=$OUT/$(printf 'jules_spinA_c%02d' $((c - 1))).dump.$((Y1 + 1))0101.0.nc
    else
      ic=$OUT/$rid.dump.${y}0101.0.nc
    fi
    if [ "$ic" != cold ] && [ ! -s $ic ]; then
      echo "STOP c$c $y: IC $ic missing"; exit 1
    fi
    write_timesteps $y
    write_ic $ic
    log=logs/${rid}_$y.log
    t0=$(date +%s)
    mpirun -np $NP $EXE > $log 2>&1
    rc=$?
    if [ $rc -ne 0 ] || grep -q FATAL $log || [ ! -s $end_dump ]; then
      echo "STOP c$c $y: rc=$rc, FATAL=$(grep -c FATAL $log), end dump $( [ -s $end_dump ] && echo ok || echo missing) -> $log"
      exit 1
    fi
    if ! python $GATE $OUT $rid $y; then
      echo "STOP c$c $y: gate failed"; exit 1
    fi
    echo "  c$c $y done in $(( $(date +%s) - t0 )) s ($(date +%H:%M)), IC=$(basename $ic)"
  done
  echo "=== cycle $c done $(date) ==="
done
echo "=== END $(date) ==="
