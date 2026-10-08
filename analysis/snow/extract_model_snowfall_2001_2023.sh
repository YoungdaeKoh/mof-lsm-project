#!/bin/bash
# Extract model-received snowfall (monthly, 2001-2023) for LM4p / CLM5 / Noah-MP (JULES outputs only total precip).
# Output: /data2/ydkoh/snowdiag/<model>_snowfall_2001_2023.nc
# Run: ssh climate "bash ~/snowdiag/extract_model_snowfall_2001_2023.sh >& ~/snowdiag/extract_sf.log"
set -e
NCO=/usr/local/nco/4.8.0/bin
OUT=/data2/ydkoh/snowdiag
cd $OUT

# LM4+ fprec_l "snowfall to land" kg/(m2 s), 1deg monthly 1979-2023; 2001-01 = index 264
$NCO/ncks -O -d time,264,539 /data2/ydkoh/lm4/postproc/lm4p_ctl/byvar/lm4p_ctl_1979-2024.fprec_l.1979-2023.1deg.nc lm4p_snowfall_2001_2023.nc

# CLM5 SNOW "atmospheric snow, after rain/snow repartitioning based on temperature" mm/s
C=/data2/ydkoh/cesm2_output/postproc/clm5_prod
for y in $(seq 2001 2023); do $NCO/ncks -O --mk_rec_dmn time -v SNOW $C/clm5_prod.$y.nc clm5sf.$y.tmp.nc; done
$NCO/ncrcat -O clm5sf.????.tmp.nc clm5_snowfall_2001_2023.nc; /bin/rm -f clm5sf.????.tmp.nc

# Noah-MP ACSNOW (postproc already converted to mm/day)
N=$HOME/HRLDAS/forcing_WFDE5_1deg/prod_1979_2023/postproc
for y in $(seq 2001 2023); do for m in 01 02 03 04 05 06 07 08 09 10 11 12; do
  $NCO/ncks -O -v ACSNOW $N/noahmp_prod_mon_$y$m.nc nmpsf.$y$m.tmp.nc; done; done
$NCO/ncrcat -O nmpsf.??????.tmp.nc noahmp_snowfall_2001_2023.nc; /bin/rm -f nmpsf.??????.tmp.nc

ls -la $OUT/*snowfall*; echo DONE
