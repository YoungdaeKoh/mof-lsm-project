#!/bin/bash
# Phenology sensitivity test for the boreal autumn LAI excess (LM4 notes 13.66/13.67).
#   base  ctl settings
#   tc10  tc_crit 278.15 -> 283.15 K for larix and c3grass (the two species that
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
VARIANTS="base tc10"
Y=2010; SEED=$C/archive/2009; NP=24
[ -d $SEED ] || SEED=$C/archive/y2009

stage() {   # $1 variant  $2 days
  D=$T/$1; rm -rf $D; mkdir -p $D/INPUT $D/RESTART $D/FORCING
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
  if [ "$1" = tc10 ]; then
    sed -i -E "s/tc_crit *= *278\.15/tc_crit = 283.15/" $D/field_table
  fi
  ln -sfn $EXE $D/model.x
  echo "$1: $MO months $DA days from $Y-01-01, seed $SEED"
}

setup() {   # $1 days
  for v in $VARIANTS; do stage $v $1; done
  echo "--- field_table diff (tc10 vs base)"; diff $T/base/field_table $T/tc10/field_table
  echo "--- input.nml diff (base vs ctl template)"; diff $C/input.nml.template $T/base/input.nml
  echo "--- SIS_layout"; grep -i "^LAYOUT" $T/base/SIS_layout
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
  mpirun -np $NP ./model.x > esm4p5.log 2>&1
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
  setup) setup "${2:-1}" ;;
  run)   run "$2" ;;
  check) check ;;
  *) echo "usage: $0 setup <days> | run <variant> | check" ;;
esac
