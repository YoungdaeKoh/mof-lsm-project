#!/bin/bash
# Extract monthly SWE and snow cover fraction (2001-2023) from the four LSM production runs on climate00.
# Output: /data2/ydkoh/snowdiag/<model>_snow_2001_2023.nc  (light, rsync to local for analysis)
# Run: ssh climate "bash ~/snowdiag/extract_snow_2001_2023.sh >& ~/snowdiag/extract.log"
set -e
NCO=/usr/local/nco/4.8.0/bin
OUT=/data2/ydkoh/snowdiag
mkdir -p $OUT; cd $OUT

# --- LM4+ ctl: already 1deg lat-lon, monthly 1979-2023 (540 records); 2001-01 = index 264
L=/data2/ydkoh/lm4/postproc/lm4p_ctl/byvar
$NCO/ncks -O -d time,264,539 $L/lm4p_ctl_1979-2024.snow.1979-2023.1deg.nc      lm4_snow.tmp.nc
$NCO/ncks -O -d time,264,539 $L/lm4p_ctl_1979-2024.snow_frac.1979-2023.1deg.nc lm4_frac.tmp.nc
$NCO/ncks -A lm4_frac.tmp.nc lm4_snow.tmp.nc
/bin/mv -f lm4_snow.tmp.nc lm4p_snow_2001_2023.nc; /bin/rm -f lm4_frac.tmp.nc

# --- CLM5 BGC prod: f09 192x288, one file per year (12 months)
C=/data2/ydkoh/cesm2_output/postproc/clm5_prod
for y in $(seq 2001 2023); do $NCO/ncks -O --mk_rec_dmn time -v H2OSNO,FSNO $C/clm5_prod.$y.nc clm5.$y.tmp.nc; done
$NCO/ncrcat -O clm5.????.tmp.nc clm5_snow_2001_2023.nc; /bin/rm -f clm5.????.tmp.nc

# --- JULES prod: land-point vector (y=1, x=17295) + latitude/longitude; frac (tile type 9 = ice) for masking
J=/data2/ydkoh/JULES_runs/prod_1979_2023/output
# (ncrcat 4.8.0 aborts with "corrupted size vs. prev_size" on these files -> keep yearly files, concatenate locally)
mkdir -p jules_yearly
for y in $(seq 2001 2023); do $NCO/ncks -O -v snow_mass_gb,snow_frac,latitude,longitude $J/jules_prod.monthly.$y.nc jules_yearly/jules_snow.$y.nc; done
/bin/rm -f jules.????.tmp.nc
$NCO/ncks -O -d time,0 -v frac,latitude,longitude $J/jules_prod.monthly.2001.nc jules_frac_2001jan.nc

# --- Noah-MP prod: 1deg lat-lon, one file per month
N=$HOME/HRLDAS/forcing_WFDE5_1deg/prod_1979_2023/postproc
for y in $(seq 2001 2023); do for m in 01 02 03 04 05 06 07 08 09 10 11 12; do
  $NCO/ncks -O -v SNEQV,FSNO $N/noahmp_prod_mon_$y$m.nc nmp.$y$m.tmp.nc; done; done
$NCO/ncrcat -O nmp.??????.tmp.nc noahmp_snow_2001_2023.nc; /bin/rm -f nmp.??????.tmp.nc

ls -la $OUT
echo DONE
