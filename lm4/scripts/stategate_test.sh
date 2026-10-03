#!/bin/bash
# Chained A/B test of the offline "gate" patches (LM4 notes 13.63):
#   base   production exe
#   gateB  update_atmos_model_state skipped (clock + diag_send_complete kept)
#   gateBC gateB + atmosphere-only remaps of flux_up_to_atmos skipped
# Two segments per variant, as the production chain does it:
#   seg1  31 days from lufix archive/y2001 (2002-01-01 03Z -> 02-01 03Z), so a
#         monthly record is written
#   seg2   5 days, started from the variant's OWN seg1 RESTART/* (2002-02-01 03Z)
# A patch passes if land restarts and land/river history are bit-for-bit equal
# to base in both segments.  Only reads the lufix run dir; writes under $T.
# usage: bash stategate_test.sh setup | run <variant> <seg1|seg2> | compare
set -u
L=/data2/ydkoh/lm4/RUN/lm4p_lufix_1979-2023
T=/data2/ydkoh/lm4/RUN/stategate_test2
EXE_base=/data2/ydkoh/lm4/esm4p5-lm4p-offline/exec/fms_esm4.5_compile_v3_1007_fix.x
EXE_gateB=/data2/ydkoh/lm4/build_gateB/fms_esm4.5_gateB.x
EXE_gateBC=/data2/ydkoh/lm4/build_gateBC/fms_esm4.5_gateBC.x
VARIANTS="base gateB gateBC"
Y=2002; SEED=$L/archive/y2001; NP=48

stage() {   # $1 variant  $2 segment  $3 days  $4 "y,m,d"  $5 restart dir
  D=$T/$1/$2; mkdir -p $D/INPUT $D/RESTART $D/FORCING
  for f in data_table diag_table field_table MOM_input MOM_layout MOM_override \
           SIS_input SIS_layout SIS_override COBALT_input COBALT_override; do
    cp -p $L/$f $D/
  done
  # static inputs: links to the lufix INPUT; restarts: links to an immutable set
  # (the live INPUT/*.res* are overwritten by the chain every year)
  ln -sf $L/INPUT/* $D/INPUT/
  for r in $5/*.res*; do ln -sf $r $D/INPUT/; done
  ln -sfn /data2/ydkoh/lm4/forcing_WFDE5_lm4p/wfde5_atm_${Y}.nc $D/FORCING/wfde5_atm.nc
  sed -e "s/^        days   = .*/        days   = $3,/" \
      -e "s/^        hours  = .*/        hours  = 0,/" \
      -e "s/^        current_date = .*/        current_date = $4,3,0,0,/" \
      $L/input.nml.template > $D/input.nml
  eval ln -sfn \$EXE_$1 $D/model.x
  echo "$1/$2: $3 days from $4, restarts -> $(dirname $(readlink $D/INPUT/cana.res.tile1.nc))"
}

setup() {
  for v in $VARIANTS; do stage $v seg1 31 "$Y,1,1" $SEED; done
}

run() {     # $1 variant  $2 segment
  if [ "$2" = seg2 ]; then
    n=$(ls $T/$1/seg1/RESTART/*.res* 2>/dev/null | wc -l)
    [ "$n" -ge 40 ] || { echo "ABORT: $1/seg1 wrote only $n restart files"; return 1; }
    stage $1 seg2 5 "$Y,2,1" $T/$1/seg1/RESTART
  fi
  D=$T/$1/$2; cd $D || exit 1
  source /etc/profile.d/modules.sh
  module purge
  module load intel21/compiler-21 intel21/mkl intel21/hdf5-1.10.5 intel21/netcdf-4.6.1 intel21/mvapich2-2.3.4
  ulimit -s unlimited
  export MV2_SMP_USE_CMA=1 MV2_IBA_EAGER_THRESHOLD=131072 MV2_ENABLE_AFFINITY=0
  echo "=== $1/$2 start $(date)"
  mpirun -np $NP ./model.x > esm4p5.log 2>&1
  echo "=== $1/$2 end rc=$? $(date)"
  grep -E '^(Total runtime|Main loop|Initialization|Land |Flux UP to atm|SFC boundary layer|FV dy-core|FV Diag)|A-L: update_atmos_model_state|Update-Land-Fast' esm4p5.log | cut -c1-80
  grep FATAL esm4p5.log | grep -v FATAL_UNUSED_PARAMS | head -3
  echo "restart files: $(ls RESTART | wc -l)"
}

compare() {
  source /home/ydkoh/anaconda3/etc/profile.d/conda.sh; conda activate
  for v in gateB gateBC; do
    for s in seg1 seg2; do
      [ -d $T/$v/$s/RESTART ] && { echo "######## base vs $v, $s"; python /data2/ydkoh/lm4/stategate_compare.py $T/base/$s $T/$v/$s; }
    done
  done
}

case "${1:-}" in
  setup) setup ;;
  run) run $2 $3 ;;
  compare) compare ;;
  *) echo "usage: $0 setup | run <variant> <seg1|seg2> | compare" ;;
esac
