#!/bin/bash
# LM4p ctl: C96 land output -> 1 deg lat-lon, one file per variable (1979-2023),
# then split into yearly files to match the CLM5 / Noah-MP layout.
# Run on climate00 under the anaconda base env.
set -u
source /home/ydkoh/anaconda3/etc/profile.d/conda.sh; conda activate

CASE=/data2/ydkoh/lm4/RUN/lm4p_ctl_1979-2024
GRID=$CASE/INPUT
OUT=/data2/ydkoh/lm4/postproc/lm4p_ctl
CONV=/data2/ydkoh/lm4/postprocess_lm4p_to_latlon.py
Y0=${1:-1979}
Y1=${2:-2023}

VARS="sens evap_land evap_soil transp grnd_flux swdn_dir swdn_dif swup_dir swup_dif \
      lwdn flw t_ref Tgrnd Trad vegn_T soil_T soil_liq soil_ice theta \
      runf frunf snow snow_frac precip fprec_l \
      lai gpp npp nep btot bwood bl br tot_soil_C fsc ssc"

mkdir -p $OUT/byvar
echo "=== per-variable regrid $Y0-$Y1 $(date)"
for v in $VARS; do
  f=$OUT/byvar/lm4p_ctl_1979-2024.$v.$Y0-$Y1.1deg.nc
  if [ -s "$f" ]; then echo "  $v already done"; continue; fi
  python $CONV --case $CASE --years $Y0 $Y1 --vars $v --res 1.0 \
         --griddir $GRID --outdir $OUT/byvar || { echo "FAILED $v"; exit 1; }
done
echo "=== per-variable done $(date)"
