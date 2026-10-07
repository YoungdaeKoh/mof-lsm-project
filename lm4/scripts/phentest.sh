#!/bin/bash
# Phenology tests for the boreal autumn LAI excess (LM4 notes 13.66/13.67/13.69).
#   base  ctl settings
#   tc10    tc_crit 278.15 -> 283.15 K for larix and c3grass (the two species that
#         override it; acer already uses the code default 283.16 K, vegn_data.F90:261).
#         tc_crit is BOTH the leaf-on gate and the cold leaf-off trigger
#         (vegn_dynamics.F90 vegn_phenology_ppa), so spring onset moves too.
# One model year 2010 from ctl archive/y2009 restarts, 24 PE on climate00
# (layout taken from the 24-PE KIOST AMIP config: fv/land 2,2, SIS 6,4, io group 8),
# gateBC exe (land bit-identical to production, LM4 notes 13.63).
# Only reads the ctl run dir; writes under $T.
# usage: bash phentest.sh setup <days> | run <variant> | check
set -u
C=/data2/ydkoh/lm4/RUN/lm4p_ctl_1979-2024
T=/data2/ydkoh/lm4/RUN/phentest
EXE=/data2/ydkoh/lm4/build_gateBC/fms_esm4.5_gateBC.x
EXE_PHENOFF=/data2/ydkoh/lm4/build_phenoff/fms_esm4.5_phenoff.x   # phenoff_build.sh
VARIANTS=${VARIANTS:-"base tc10"}
#   noparam phenoff exe, ctl field_table (regression: must equal base bit for bit)
#   offon   phenoff exe, larix/c3grass tc_crit_off=283.15 K, dayl_crit_off=14 h (13.69)
#   dayl    phenoff exe, day-length-led leaf-off: larix/c3grass dayl_crit_off=13 h, acer 12 h,
#           tc_crit_off=293.15 K for all three (notes 13.70, experiment 4)
#   dayl2   phenoff exe, type-specific thresholds: larix 13.5 h, c3grass 12.5 h, acer 11.5 h,
#           tc_crit_off=293.15 K (notes 13.70, experiment 5); submit with phentest_pbs.sh on climate01
#   replant  CTRL settings (gateBC exe, ctl field_table) started from the relabelled restart
#           /data2/ydkoh/lm4/RUN/replant_seed (species from the CLM5 map, replant_step3_relabel.py);
#           any variant can start elsewhere with SEED=<dir>
#   <variant>_d  same as <variant> plus daily LAI in the land_daily stream (diag only,
#           e.g. base_d, offon_d; used for day-resolved SOS/EOS on the poster)
Y=2010; NP=24
SEED=${SEED:-$C/archive/y2009}            # override with SEED=<dir> (e.g. the replanted restart)

stage() {   # $1 variant  $2 days
  D=$T/$1
  # never wipe a finished run by accident: a run that wrote its end-of-run restart is kept
  # unless FORCE=1 is given (LM4 notes 13.70, raw results are not reproducible for free)
  if [ -s $D/RESTART/coupler.res ] && [ "${FORCE:-0}" != 1 ]; then
    echo "REFUSING to re-stage $1: $D holds a finished run (end $(tail -1 $D/RESTART/coupler.res | awk '{print $1"-"$2"-"$3}')). Use FORCE=1 to overwrite."; exit 1
  fi
  rm -rf $D; mkdir -p $D/INPUT $D/RESTART $D/FORCING
  for f in data_table diag_table field_table MOM_input MOM_layout MOM_override \
           SIS_input SIS_layout SIS_override COBALT_input COBALT_override; do
    [ -e $C/$f ] && cp -p $C/$f $D/
  done
  ln -sf $C/INPUT/* $D/INPUT/
  for r in $SEED/*.res*; do ln -sf $r $D/INPUT/; done
  ln -sfn /data2/ydkoh/lm4/forcing_WFDE5_lm4p/wfde5_atm_${Y}.nc $D/FORCING/wfde5_atm.nc
  if [ "$2" -ge 365 ]; then MO=12; DA=0; else MO=0; DA=$2; fi
  sed -e "s/^        months = .*/        months = $MO,/" \
      -e "s/^        days   = .*/        days   = $DA,/" \
      -e "s/^        hours  = .*/        hours  = 0,/" \
      -e "s/^        current_date = .*/        current_date = $Y,1,1,3,0,0,/" \
      -e "s/^        atmos_npes = 48/        atmos_npes = $NP/" \
      -e "s/^        layout   = 2,4/        layout   = 2,2/" \
      -e "s/^       layout   = 2,4/       layout   = 2,2/" \
      -e "s/^       npes_io_group = 48/       npes_io_group = 8/" \
      $C/input.nml.template > $D/input.nml
  sed -i "s/^LAYOUT    = 6,8/LAYOUT    = 6,4/" $D/SIS_layout
  K=${1%_d}   # variant kind without the daily-output suffix
  if [ "$K" = tc10 ]; then
    sed -i -E "s/tc_crit *= *278\.15/tc_crit = 283.15/" $D/field_table
  fi
  if [ "$K" = offon ]; then
    sed -i -E "s/^( *)tc_crit *= *278\.15.*/&\n\1tc_crit_off = 283.15\n\1dayl_crit_off = 14.0/" $D/field_table
  fi
  if [ "$K" = dayl ]; then
    # experiment 4: day length sets the leaf-off date; the 20 C cap only keeps tropical grass on
    sed -i -E "s/^( *)tc_crit *= *278\.15.*/&\n\1tc_crit_off = 293.15\n\1dayl_crit_off = 13.0/" $D/field_table
    sed -i -E '/"species", *"land_mod", *"acer"/{n;s/$/\n    tc_crit_off = 293.15\n    dayl_crit_off = 12.0/}' $D/field_table
  fi
  if [ "$K" = dayl2 ]; then
    # experiment 5: thresholds from the observed EOS of each vegetation type (notes 13.70):
    # larch 13.5 h, C3 grass 12.5 h, deciduous broadleaf 11.5 h; same 20 C cap
    sed -i -E '/"species", *"land_mod", *"larix"/,/"species", *"land_mod", *"acer"/ s/^( *)tc_crit *= *278\.15.*/&\n\1tc_crit_off = 293.15\n\1dayl_crit_off = 13.5/' $D/field_table
    sed -i -E '/"species", *"land_mod", *"c3grass"/,$ s/^( *)tc_crit *= *278\.15.*/&\n\1tc_crit_off = 293.15\n\1dayl_crit_off = 12.5/' $D/field_table
    sed -i -E '/"species", *"land_mod", *"acer"/{n;s/$/\n    tc_crit_off = 293.15\n    dayl_crit_off = 11.5/}' $D/field_table
  fi
  if [ "$1" != "$K" ]; then
    sed -i '/^"land", "precip", "precip", "land_daily"/a "vegn", "lai", "lai", "land_daily", "all", .true., "none", 2' $D/diag_table
  fi
  case $K in noparam|offon|dayl|dayl2) ln -sfn $EXE_PHENOFF $D/model.x ;; *) ln -sfn $EXE $D/model.x ;; esac
  echo "$1: $MO months $DA days from $Y-01-01, seed $SEED"
}

setup() {   # $1 days
  for v in $VARIANTS; do stage $v $1; done
  for v in $VARIANTS; do echo "--- field_table diff ($v vs ctl)"; diff $C/field_table $T/$v/field_table; echo "    exe -> $(readlink $T/$v/model.x)"; echo "    diag_table diff:"; diff $C/diag_table $T/$v/diag_table; done
  v1=${VARIANTS%% *}; echo "--- input.nml diff ($v1 vs ctl template)"; diff $C/input.nml.template $T/$v1/input.nml
  echo "--- SIS_layout"; grep -i "^LAYOUT" $T/$v1/SIS_layout
  echo "--- seed date"; cat $SEED/coupler.res 2>/dev/null | tail -2
}

run() {     # $1 variant
  D=$T/$1; cd $D || exit 1
  source /etc/profile.d/modules.sh
  module purge
  module load intel21/compiler-21 intel21/mkl intel21/hdf5-1.10.5 intel21/netcdf-4.6.1 intel21/mvapich2-2.3.4
  ulimit -s unlimited
  export MV2_SMP_USE_CMA=1 MV2_IBA_EAGER_THRESHOLD=131072 MV2_ENABLE_AFFINITY=0
  echo "=== $1 start $(date)"
  # under PBS pass HOSTFILE=$PBS_NODEFILE so the ranks land on the allocated node (pbs-alloc-vs-mpirun-hostfile)
  nice -n 10 mpirun ${HOSTFILE:+-hostfile $HOSTFILE} -np $NP ./model.x > esm4p5.log 2>&1
  echo "=== $1 end rc=$? $(date)"
  grep -E '^(Total runtime|Main loop)' esm4p5.log | cut -c1-80
}

check() {
  for v in $VARIANTS; do
    D=$T/$v
    echo "$v: restarts $(ls $D/RESTART 2>/dev/null | wc -l), date $(tail -1 $D/RESTART/coupler.res 2>/dev/null), FATAL $(grep -c FATAL $D/esm4p5.log 2>/dev/null)"
  done
}

case "${1:-}" in
  setup) setup "${2:-1}" ;;   # VARIANTS="noparam" bash phentest.sh setup 31
  run)   run "$2" ;;
  check) check ;;
  *) echo "usage: $0 setup <days> | run <variant> | check" ;;
esac
