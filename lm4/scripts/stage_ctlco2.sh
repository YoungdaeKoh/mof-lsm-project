#!/bin/bash
# Stage an LM4p offline run = ctl production (LU change ON) + historical CMIP7 CO2 via data_override "co2_bot"
# (user decision 2026-10-10, notes/decisions.md; code path atm_land_ice_flux_exchange.F90:897).
#   usage: bash stage_ctlco2.sh <run_name> [test]
#     test : 31-day segment from 1979-01-01 03Z (check qco2_dvmr ~ 337.7 ppm)
#     else : input.nml.template only; drive with chain_lm4p_ctl.sh (R=<run dir>) 1979..2023
#   physics/config = ctl production (same exe, land-use change ON from the ctl template)
#                    + offline_fast field/diag tables (land physics bit-identical, LM4 notes 13.71; diag + qco2_dvmr)
#   seed = END OF CYCLE 2 = ctl archive/y2010 restarts (2011-01-01), clock rewound to 1979 -> this run is cycle 3
#          (user 2026-10-10). landuse.res date set to 1979 (LM4 notes 13.47; transitions are deltas, no double count).
# Safety: INPUT is symlinked to the ctl INPUT; restart links are removed BEFORE the seed restarts are copied in.
set -eu
NAME=$1; MODE=${2:-chain}
C=/data2/ydkoh/lm4/RUN/lm4p_ctl_1979-2024
CFG=/data2/ydkoh/lm4/RUN/config                    # offline_fast tables + co2 file staged here from git
R=/data2/ydkoh/lm4/RUN/$NAME
CO2=$CFG/co2_latlon_cmip7_1978_2024.nc
[ -e "$R" ] && { echo "REFUSING: $R exists"; exit 1; }
for f in $CFG/field_table.offline_fast $CFG/diag_table.offline_fast $CO2; do [ -s $f ] || { echo "ABORT: missing $f"; exit 1; }; done
grep -q '"qco2_dvmr"' $CFG/diag_table.offline_fast || { echo "ABORT: diag_table lacks qco2_dvmr"; exit 1; }
mkdir -p $R/INPUT $R/RESTART $R/FORCING

for f in data_table MOM_input MOM_layout MOM_override SIS_input SIS_layout SIS_override COBALT_input COBALT_override input.nml.template; do
  [ -e $C/$f ] && cp -p $C/$f $R/
done
cp -p $CFG/field_table.offline_fast $R/field_table
cp -p $CFG/diag_table.offline_fast  $R/diag_table
grep -q '"co2_bot"' $R/data_table && { echo "ABORT: data_table already has co2_bot"; exit 1; }
cat >> $R/data_table <<'EOT'
# 2026-10-10: historical CO2 to the land via the bottom atmospheric tracer (offline: atmos_co2 restore never runs,
# so co2_dvmr_restore above is unused). Dry vmr in ppm x 1e-6; flux_exchange converts to moist mmr.
"ATM", "co2_bot", "co2", "./INPUT/co2_latlon.nc", "bilinear", 1.0e-6
EOT
ln -sfn "$(readlink -f $C/fms_esm4.5_compile_v3_1007_fix.x)" $R/fms_esm4.5_compile_v3_1007_fix.x

ln -sf $C/INPUT/* $R/INPUT/
SEED=${SEED:-$C/archive/y2010}
[ "$(tail -1 $SEED/coupler.res | awk '{print $1"-"$2"-"$3}')" = "2011-1-1" ] || { echo "ABORT: $SEED is not 2011-01-01"; exit 1; }
n=0
for r in $SEED/*.res*; do
  b=$(basename $r); rm -f $R/INPUT/$b; cp -p $r $R/INPUT/$b; n=$((n + 1))
done
# rewind blocker (13.47): previous land-use transition time must not be later than the start time
/bin/mv -f $R/INPUT/landuse.res $R/INPUT/landuse.res.orig2011
echo "  1979     1     1     0     0     0        Time of previous landuse transition calculation" > $R/INPUT/landuse.res
rm -f $R/INPUT/co2_latlon.nc; cp -p $CO2 $R/INPUT/co2_latlon.nc
echo "copied $n seed restarts ($SEED) + co2_latlon.nc into $R/INPUT; landuse.res -> 1979"

sed -e "s#^export work_dir=.*#export work_dir=$R#" -e "s#^\#PBS -N lm4p_ctl#\#PBS -N ctlco2#" \
    -e "s#lm4p_ctl.err#ctlco2.err#; s#lm4p_ctl.log#ctlco2.log#" $C/run_lm4p_ctl.sh > $R/run_lm4p_ctl.sh
chmod +x $R/run_lm4p_ctl.sh

if [ "$MODE" = test ]; then
  sed -e "s/^        days   = .*/        days   = 31,/" -e "s/^        hours  = .*/        hours  = 0,/" \
      -e "s/^        current_date = .*/        current_date = 1979,1,1,3,0,0,/" $R/input.nml.template > $R/input.nml
  ln -sfn /data2/ydkoh/lm4/forcing_WFDE5_lm4p/wfde5_atm_1979.nc $R/FORCING/wfde5_atm.nc
  echo "test staged: qsub $R/run_lm4p_ctl.sh"
fi
{ echo "### data_table diff (ctl -> $NAME)"; diff $C/data_table $R/data_table;
  echo "### field_table diff"; diff $C/field_table $R/field_table | head -5; echo "### diag_table: offline_fast + qco2_dvmr"; } > $R/config_diff.txt || true
echo "staged $R ($MODE)"
