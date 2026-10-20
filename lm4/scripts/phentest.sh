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
EXE_SPRING=/data2/ydkoh/lm4/build_phenspring2/fms_esm4.5_phenspring2.x   # phenoff patch + tau_pheno_on (lm4P.phenology_spring_tau.diff)
EXE_HOLD=/data2/ydkoh/lm4/build_phenhold/fms_esm4.5_phenhold.x   # phenspring2 + winter hold dayl_crit_on (2026-10-19)
EXE_LAT=/data2/ydkoh/lm4/build_phenlat/fms_esm4.5_phenlat.x   # phenhold + latitude-dependent autumn threshold (2026-10-20)
# (build_phenspring, 2026-10-14, is the flawed first version: 5-day leaf-on undone next day by the 20-day cold leaf-off
#  and GDD reset -> leaf-on 8 d LATER; its result is kept as phentest/daylspring5_bug_d)
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
# DEFAULT CONFIG (2026-10-08): every variant except the four speed tests below now starts from the fast
#   offline tables config/field_table.offline_fast + config/diag_table.offline_fast (-23 % wall time at 48 ranks,
#   land output bit-identical); FULLCFG=1 reverts to the ctl tables. Runs staged before this date used the ctl tables.
# Offline speed tests (LM4 notes 13.71; all gateBC exe, ctl physics, run 31 days via phentest_pbs_chain.sh):
#   ctrl1m  ctl settings (timing baseline; same as base but its own 1-month directory)
#   ddep1m  ctrl1m + every "dry_deposition" line removed from field_table (atmos_mod and land_mod)
#           -> land_tracer_driver sets do_deposition=F for all generic tracers; tracers themselves stay
#   diag1m  ddep1m + diag_table replaced by config/diag_table.offline_min (make_diag_table_min.py)
#   cons1m  diag1m + water_cons/carbon_cons also dropped (config/diag_table.offline_min_nocons)
Y=2010; NP=24
# decomposition suffixes (offline speed tests, LM4 notes 13.71); combine after the kind, before _d:
#   _np48  48 ranks with the production layout (template unchanged); submit with ncpus=48
#   _l14 / _l41  24 ranks, land layout 1,4 / 4,1 per cube face instead of 2,2
npcfg() { NP=24; LL=""; case $1 in *_np48*) NP=48 ;; esac; case $1 in *_l14*) LL=1,4 ;; *_l41*) LL=4,1 ;; esac; }
kind()  { local k=${1%_d}; k=${k%_np48}; k=${k%_l14}; k=${k%_l41}; echo $k; }
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
  # phasewfde5 (2026-10-20): same as base (CTRL, gateBC exe) but the forcing takes snow/rain from WFDE5 Snowf/Rainf
  #   instead of the 0-2 C TBOT ramp (lm4p_offline_wfde5_to_atm.py <y> wfde5); every other forcing field identical
  FSUF=""; case $1 in phasewfde5*) FSUF=_phasewfde5 ;; esac
  ln -sfn /data2/ydkoh/lm4/forcing_WFDE5_lm4p/wfde5_atm_${Y}${FSUF}.nc $D/FORCING/wfde5_atm.nc
  [ -e $D/FORCING/wfde5_atm.nc ] || { echo "missing forcing wfde5_atm_${Y}${FSUF}.nc"; exit 1; }
  if [ "$2" -ge 365 ]; then MO=12; DA=0; else MO=0; DA=$2; fi
  npcfg $1
  if [ "$NP" = 48 ]; then   # production decomposition, template unchanged (fv/land 2,4, SIS 6,8, io group 48)
    sed -e "s/^        months = .*/        months = $MO,/" \
        -e "s/^        days   = .*/        days   = $DA,/" \
        -e "s/^        hours  = .*/        hours  = 0,/" \
        -e "s/^        current_date = .*/        current_date = $Y,1,1,3,0,0,/" \
        $C/input.nml.template > $D/input.nml
  else
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
  fi
  # land decomposition per cube face (&land_model_nml is the second "layout" line, 7-space indent)
  [ -n "$LL" ] && sed -i "s/^       layout   = 2,2/       layout   = $LL/" $D/input.nml
  K=$(kind $1)   # variant kind without the daily-output / decomposition suffixes
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
  # spring5 (2026-10-14): CTRL autumn, leaf-on tested on a 5-day smoothed temperature (vegn_dynamics_nml
  #   tau_pheno_on = 5, phenspring exe; default tc_pheno ~20 d delays leaf-on by 3-4 weeks, spring_gate_diag.py)
  # daylspring5: dayl (DL13/12 autumn) + the same spring change
  # daylhold5 (2026-10-19): daylspring5 + winter hold, leaf-on blocked while day length < 12 h and tc_pheno < 20 C
  #   (dayl_crit_on = 12 for larix/acer/c3grass; stops mid-winter re-greening, dl_dormancy_latch_offline.py)
  if [ "$K" = spring5 ] || [ "$K" = daylspring5 ] || [ "$K" = daylhold5 ]; then
    printf '\n &vegn_dynamics_nml\n    tau_pheno_on = %s\n /\n' "${TAU:-5.0}" >> $D/input.nml   # TAU=<days> overrides
  fi
  if [ "$K" = dayl2 ]; then
    # experiment 5: thresholds from the observed EOS of each vegetation type (notes 13.70):
    # larch 13.5 h, C3 grass 12.5 h, deciduous broadleaf 11.5 h; same 20 C cap
    sed -i -E '/"species", *"land_mod", *"larix"/,/"species", *"land_mod", *"acer"/ s/^( *)tc_crit *= *278\.15.*/&\n\1tc_crit_off = 293.15\n\1dayl_crit_off = 13.5/' $D/field_table
    sed -i -E '/"species", *"land_mod", *"c3grass"/,$ s/^( *)tc_crit *= *278\.15.*/&\n\1tc_crit_off = 293.15\n\1dayl_crit_off = 12.5/' $D/field_table
    sed -i -E '/"species", *"land_mod", *"acer"/{n;s/$/\n    tc_crit_off = 293.15\n    dayl_crit_off = 11.5/}' $D/field_table
  fi
  # larixlma (2026-10-14): larix LMA 0.076 -> 0.038 kgC m-2 (the commented-out value in the same block;
  # literature 0.026-0.046, Fellner et al. 2016). Applied after the fast-config copy below. Use with SEED=replant_seed.
  # default since 2026-10-08: fast offline config (LM4 notes 13.71; land physics bit-identical to ctl):
  # field_table without dry deposition, diag_table = config/diag_table.offline_fast. FULLCFG=1 keeps the ctl tables.
  # The speed-test variants below keep their own definitions.
  case $K in ctrl1m|ddep1m|diag1m|cons1m) ;;
    *) if [ "${FULLCFG:-0}" != 1 ]; then cp -p $T/../config/field_table.offline_fast $D/field_table
                                         cp -p $T/../config/diag_table.offline_fast  $D/diag_table; fi ;; esac
  case $K in ddep1m|diag1m|cons1m) sed -i '/"dry_deposition"/d' $D/field_table ;; esac
  # NOTE (2026-10-14): the tc10/offon/dayl/dayl2 field_table edits above run BEFORE this fast-config copy and are
  # overwritten by it; those variants were staged before 2026-10-08 (ctl tables). Re-staging them needs FULLCFG=1
  # or moving their edits below. New variants put their field_table edits here, after the copy.
  if [ "$K" = daylspring5 ] || [ "$K" = daylhold5 ]; then   # experiment 4 (DL13/12) autumn settings, as in dayl
    sed -i -E "s/^( *)tc_crit *= *278\.15.*/&\n\1tc_crit_off = 293.15\n\1dayl_crit_off = 13.0/" $D/field_table
    sed -i -E '/"species", *"land_mod", *"acer"/{n;s/$/\n    tc_crit_off = 293.15\n    dayl_crit_off = 12.0/}' $D/field_table
  fi
  # dayllat (2026-10-20): autumn rule only, threshold 12.0 + 0.05 (|lat| - 40) h for larix/acer/c3grass
  #   (s7_eos_daylength_lat_fit.py, autumn_latrule_offline.py); spring = CTRL, as dayl -> compare with dayl_d
  if [ "$K" = dayllat ]; then
    sed -i -E "s/^( *)tc_crit *= *278\.15.*/&\n\1tc_crit_off = 293.15\n\1dayl_crit_off = 12.0/" $D/field_table
    sed -i -E '/"species", *"land_mod", *"acer"/{n;s/$/\n    tc_crit_off = 293.15\n    dayl_crit_off = 12.0/}' $D/field_table
    sed -i -E "s/^( *)dayl_crit_off *= *.*/&\n\1dayl_off_slope = 0.05\n\1dayl_off_lat0 = 40.0/" $D/field_table
  fi
  if [ "$K" = daylhold5 ]; then
    sed -i -E "s/^( *)dayl_crit_off *= *.*/&\n\1dayl_crit_on = 12.0/" $D/field_table
  fi
  if [ "$K" = larixlma ]; then
    sed -i -E '/"species", *"land_mod", *"larix"/,/"species", *"land_mod", *"acer"/ s/^ *LMA *= *0\.76e-01/    LMA =   0.38e-01/' $D/field_table
  fi
  case $K in diag1m) cp -p $T/../config/diag_table.offline_min        $D/diag_table ;;
             cons1m) cp -p $T/../config/diag_table.offline_min_nocons $D/diag_table ;; esac
  if [ "${1%_d}" != "$1" ]; then
    sed -i '/^"land", "precip", "precip", "land_daily"/a "vegn", "lai", "lai", "land_daily", "all", .true., "none", 2' $D/diag_table
  fi
  # dayllat (2026-10-20): albedo-snow-vegetation diagnostics for the spring/autumn transitions (diag only):
  #   daily albedo_dir/dif, snow_frac, snow_depth; monthly albedo_dir/dif (absent from the fast table, present in dayl_d)
  #   (also for phasewfde5: the snow-phase test needs daily snow)
  if [ "$K" = dayllat ] || [ "$K" = phasewfde5 ]; then
    for v in albedo_dir albedo_dif snow_frac snow_depth; do
      sed -i "/^\"vegn\", \"lai\", \"lai\", \"land_daily\"/a \"land\", \"$v\", \"$v\", \"land_daily\", \"all\", .true., \"none\", 2" $D/diag_table
    done
    for v in albedo_dir albedo_dif; do
      sed -i "/^\"land\", \"snow_frac\", \"snow_frac\", \"land_month\"/a \"land\", \"$v\", \"$v\", \"land_month\", \"all\", .true., \"none\", 2" $D/diag_table
    done
  fi
  if [ "$K" = phasewfde5 ]; then   # received snowfall and snowmelt (dropped from the fast table), monthly
    for v in fprec_l melts; do
      sed -i "/^\"land\", \"snow_frac\", \"snow_frac\", \"land_month\"/a \"land\", \"$v\", \"$v\", \"land_month\", \"all\", .true., \"none\", 2" $D/diag_table
    done
  fi
  # keep the configuration diff of every variant next to the run for the record
  { echo "### field_table diff (ctl -> $1)"; diff $C/field_table $D/field_table; echo "### diag_table diff (ctl -> $1)"; diff $C/diag_table $D/diag_table; } > $D/config_diff.txt
  case $K in noparam|offon|dayl|dayl2) ln -sfn $EXE_PHENOFF $D/model.x ;;
             spring5|daylspring5) ln -sfn $EXE_SPRING $D/model.x ;; daylhold5) ln -sfn $EXE_HOLD $D/model.x ;; dayllat) ln -sfn $EXE_LAT $D/model.x ;; *) ln -sfn $EXE $D/model.x ;; esac
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
  npcfg $1
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
