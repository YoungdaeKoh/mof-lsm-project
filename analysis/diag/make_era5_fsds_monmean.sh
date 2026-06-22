#!/bin/bash
# Build monthly-mean FSDS from the 6-hourly ERA5->CLM forcing files (1979-1987).
# The raw {year}_era5.nc have time as a FIXED dim, so cdo can't see the time axis
# (monmean collapses to 1 step). Fix: ncks --mk_rec_dmn time, then cdo monmean.
# Output: fsds_mon_{year}.nc  (12 months, 0.5deg, FSDS + LATIXY/LONGXY)
set -u
NCKS=/usr/local/nco/4.8.0_gcc85/bin/ncks
CDO=/usr/local/cdo/1.9.3_gcc85/bin/cdo
cd /data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM/tmp || exit 1

for y in 1979 1980 1981 1982 1983 1984 1985 1986 1987; do
  $NCKS -O -v FSDS,LATIXY,LONGXY --mk_rec_dmn time "${y}_era5.nc" "rec_${y}.nc"
  $CDO -s selname,FSDS -monmean "rec_${y}.nc" "fsds_mon_${y}.nc"
  rm -f "rec_${y}.nc"
  echo "done $y: $($CDO -s ntime fsds_mon_${y}.nc) months"
done

# cleanup scratch from earlier tests
rm -f test_1980_fsds_mon.nc t2_1980.nc m1980.nc
echo "ALL DONE"
