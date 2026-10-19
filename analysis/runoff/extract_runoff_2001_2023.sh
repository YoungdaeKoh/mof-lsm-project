#!/bin/bash
# Extract monthly runoff (2001-2023) from the four LSM production runs on climate00.
# Common quantity = LIQUID total runoff (memory lsm-runoff-definition-mismatch):
#   LM4p  runf - frunf (kg m-2 s-1; runf includes solid)   CLM5 QRUNOFF (+QOVER, QDRAI) mm/s
#   Noah-MP SFCRNOFF + UGDRNOFF (postproc already mm/day)   JULES runoff (+surf_roff, sub_surf_roff) kg m-2 s-1
# Output: /data2/ydkoh/runoffdiag/<model>_runoff_2001_2023.nc (JULES: yearly files, ncrcat 4.8.0 aborts on them)
# Run: ssh climate "bash ~/runoffdiag/extract_runoff_2001_2023.sh >& ~/runoffdiag/extract.log"
set -e
NCO=/usr/local/nco/4.8.0/bin
OUT=/data2/ydkoh/runoffdiag
mkdir -p $OUT/jules_yearly; cd $OUT

# LM4+ ctl: 1deg monthly 1979-2023 (540 records); 2001-01 = index 264
L=/data2/ydkoh/lm4/postproc/lm4p_ctl/byvar
$NCO/ncks -O -d time,264,539 $L/lm4p_ctl_1979-2024.runf.1979-2023.1deg.nc  lm4_runf.tmp.nc
$NCO/ncks -O -d time,264,539 $L/lm4p_ctl_1979-2024.frunf.1979-2023.1deg.nc lm4_frunf.tmp.nc
$NCO/ncks -A lm4_frunf.tmp.nc lm4_runf.tmp.nc
/bin/mv -f lm4_runf.tmp.nc lm4p_runoff_2001_2023.nc; /bin/rm -f lm4_frunf.tmp.nc

# CLM5 BGC prod: f09, one file per year (time not a record dim -> --mk_rec_dmn)
C=/data2/ydkoh/cesm2_output/postproc/clm5_prod
for y in $(seq 2001 2023); do $NCO/ncks -O --mk_rec_dmn time -v QRUNOFF,QOVER,QDRAI $C/clm5_prod.$y.nc clm5ro.$y.tmp.nc; done
$NCO/ncrcat -O clm5ro.????.tmp.nc clm5_runoff_2001_2023.nc; /bin/rm -f clm5ro.????.tmp.nc

# Noah-MP: 1deg (centres x.25, lon wraps -> lon%360 when reading), one file per month
N=$HOME/HRLDAS/forcing_WFDE5_1deg/prod_1979_2023/postproc
for y in $(seq 2001 2023); do for m in 01 02 03 04 05 06 07 08 09 10 11 12; do
  $NCO/ncks -O -v SFCRNOFF,UGDRNOFF $N/noahmp_prod_mon_$y$m.nc nmpro.$y$m.tmp.nc; done; done
$NCO/ncrcat -O nmpro.??????.tmp.nc noahmp_runoff_2001_2023.nc; /bin/rm -f nmpro.??????.tmp.nc

# JULES: land-point vector + latitude/longitude, yearly files
J=/data2/ydkoh/JULES_runs/prod_1979_2023/output
for y in $(seq 2001 2023); do
  $NCO/ncks -O -v runoff,surf_roff,sub_surf_roff,latitude,longitude $J/jules_prod.monthly.$y.nc jules_yearly/jules_runoff.$y.nc
done

ls -la $OUT $OUT/jules_yearly | tail -6; echo DONE
