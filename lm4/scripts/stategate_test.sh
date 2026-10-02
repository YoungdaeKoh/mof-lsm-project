#!/bin/bash
# 5-day A/B test of the atmos_state_gate patch: same restart, forcing and
# namelists, production exe (base) vs gated exe (gate), 48 ranks on this node.
# Start state = lufix archive/y2001 (end of 2001, immutable) -> 2002-01-01 03Z.
# Only reads the lufix run dir; everything is written under $T.
# usage: bash stategate_test.sh setup | run base | run gate | compare
set -u
L=/data2/ydkoh/lm4/RUN/lm4p_lufix_1979-2023
T=/data2/ydkoh/lm4/RUN/stategate_test
EXE_base=/data2/ydkoh/lm4/esm4p5-lm4p-offline/exec/fms_esm4.5_compile_v3_1007_fix.x
EXE_gate=/data2/ydkoh/lm4/build_stategate/fms_esm4.5_stategate.x
EXE_gateC=/data2/ydkoh/lm4/build_stategateC/fms_esm4.5_stategateC.x
Y=2002; SEED=$L/archive/y2001; NP=48; DAYS=5

setup() {
  for v in base gate gateC; do
    D=$T/$v; mkdir -p $D/INPUT $D/RESTART $D/FORCING
    for f in data_table diag_table field_table MOM_input MOM_layout MOM_override \
             SIS_input SIS_layout SIS_override COBALT_input COBALT_override; do
      cp -p $L/$f $D/
    done
    # static inputs: links to the lufix INPUT; restarts: links to the archived
    # year (the live INPUT/*.res* are overwritten by the chain every year)
    ln -sf $L/INPUT/* $D/INPUT/
    for r in $SEED/*.res*; do ln -sf $r $D/INPUT/; done
    ln -sfn /data2/ydkoh/lm4/forcing_WFDE5_lm4p/wfde5_atm_${Y}.nc $D/FORCING/wfde5_atm.nc
    sed -e "s/^        days   = .*/        days   = $DAYS,/" \
        -e "s/^        hours  = .*/        hours  = 0,/" \
        -e "s/^        current_date = .*/        current_date = ${Y},1,1,3,0,0,/" \
        $L/input.nml.template > $D/input.nml
    eval ln -sfn \$EXE_$v $D/model.x
    echo "$v: $(ls $D/INPUT | wc -l) inputs, restarts -> $(readlink $D/INPUT/cana.res.tile1.nc)"
  done
  diff $T/base/input.nml $T/gate/input.nml && diff $T/base/input.nml $T/gateC/input.nml && echo "namelists identical"
}

run() {
  D=$T/$1; cd $D || exit 1
  source /etc/profile.d/modules.sh
  module purge
  module load intel21/compiler-21 intel21/mkl intel21/hdf5-1.10.5 intel21/netcdf-4.6.1 intel21/mvapich2-2.3.4
  ulimit -s unlimited
  export MV2_SMP_USE_CMA=1 MV2_IBA_EAGER_THRESHOLD=131072 MV2_ENABLE_AFFINITY=0
  echo "=== $1 start $(date)"
  mpirun -np $NP ./model.x > esm4p5.log 2>&1
  echo "=== $1 end rc=$? $(date)"
  grep -E '^(Total runtime|Main loop|Initialization)|update_atmos_model_state|Update-Land-Fast|FV dy-core|FV Diag|Flux UP to atm|SFC boundary layer' esm4p5.log | cut -c1-80
  grep FATAL esm4p5.log | grep -v FATAL_UNUSED_PARAMS | head -3
  ls RESTART | wc -l
}

compare() {
  source /home/ydkoh/anaconda3/etc/profile.d/conda.sh; conda activate
  for v in gate gateC; do [ -d $T/$v/RESTART ] && { echo "######## base vs $v"; python /data2/ydkoh/lm4/stategate_compare.py $T/base $T/$v; }; done
}

case "${1:-}" in
  setup) setup ;;
  run) run $2 ;;
  compare) compare ;;
  *) echo "usage: $0 setup | run base|gate | compare" ;;
esac
