#!/bin/bash
# Post-process Noah-MP prod_1979_2023 LDASOUT: one month at a time, Y0..Y1.
# Usage: bash pp_years.sh Y0 Y1        (log: postproc/pp_YEARS.log)
set -u
source /home/ydkoh/anaconda3/etc/profile.d/conda.sh; conda activate
R=/home/ydkoh/HRLDAS/forcing_WFDE5_1deg/prod_1979_2023
cd "$R"
Y0=${1:?year0}; Y1=${2:?year1}
for y in $(seq "$Y0" "$Y1"); do
  for m in $(seq 1 12); do
    f=postproc/noahmp_prod_mon_${y}$(printf %02d $m).nc
    d=postproc/noahmp_prod_day_${y}$(printf %02d $m).nc
    if [ -s "$f" ] && [ -s "$d" ]; then echo "=== $y-$m already done, skipping"; continue; fi
    echo "=== $y-$m $(date)"
    python ldasout_6h_to_daymon.py "$y" "$m" --daily || { echo "FAILED $y-$m"; exit 1; }
  done
done
echo "=== ALL DONE $Y0-$Y1 $(date)"
