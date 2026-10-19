#!/bin/bash
# Stage the multi-year continuation of the replanted run (LM4 notes 13.71, user decision 2026-10-08:
# 5 years 2011-2015 first, then decide the spin-up length).
#   physics/config = replant1y_np48_d (CTRL phenology, gateBC exe, offline_fast tables, daily LAI)
#   initial state  = replant1y_np48_d/RESTART (2011-01-01 03Z)
#   driven by       chain_lm4p_ctl.sh with R=<this dir> (one year per PBS job, 48 PE on climate01, raw archived)
# Safety: INPUT is filled with symlinks into the ctl production INPUT; the restart links are REMOVED before
# the replant restarts are copied in -- cp onto a symlink would write through it into the ctl run.
set -eu
C=/data2/ydkoh/lm4/RUN/lm4p_ctl_1979-2024          # ctl production: template, INPUT, run script
P=/data2/ydkoh/lm4/RUN/phentest/replant1y_np48_d    # source of config + initial restart
R=/data2/ydkoh/lm4/RUN/replant_2011_2015
EXE=/data2/ydkoh/lm4/build_gateBC/fms_esm4.5_gateBC.x

[ -e "$R" ] && { echo "REFUSING: $R exists"; exit 1; }
[ "$(tail -1 $P/RESTART/coupler.res | awk '{print $1"-"$2"-"$3}')" = "2011-1-1" ] || { echo "ABORT: $P restart is not 2011-01-01"; exit 1; }
mkdir -p $R/INPUT $R/RESTART $R/FORCING

for f in data_table diag_table field_table MOM_input MOM_layout MOM_override \
         SIS_input SIS_layout SIS_override COBALT_input COBALT_override config_diff.txt; do
  [ -e $P/$f ] && cp -p $P/$f $R/
done
cp -p $C/input.nml.template $R/input.nml.template      # chain sets days/hours/current_date per year
ln -sfn $EXE $R/model.x

ln -sf $C/INPUT/* $R/INPUT/
n=0
for r in $P/RESTART/*.res*; do
  b=$(basename $r)
  rm -f $R/INPUT/$b                                    # drop the link first (never write through it)
  cp -p $r $R/INPUT/$b
  n=$((n + 1))
done
echo "copied $n replant restarts into $R/INPUT"

# run script = ctl production one, pointed at this directory and the gateBC exe
sed -e "s#^export work_dir=.*#export work_dir=$R#" \
    -e "s#^\#PBS -N lm4p_ctl#\#PBS -N replant5y#" \
    -e "s#\./fms_esm4.5_compile_v3_1007_fix.x#./model.x#" \
    -e "s#lm4p_ctl.err#replant5y.err#; s#lm4p_ctl.log#replant5y.log#" \
    $C/run_lm4p_ctl.sh > $R/run_lm4p_ctl.sh
chmod +x $R/run_lm4p_ctl.sh
echo "staged $R"
