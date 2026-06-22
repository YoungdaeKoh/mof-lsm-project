#!/bin/bash
# Monthly-mean of TBOT/PRECTmms/FLDS/WIND/QBOT from 1980_era5.nc (single-var
# selname per cdo call — multi-var monmean corrupts the file).
NCKS=/usr/local/nco/4.8.0_gcc85/bin/ncks
CDO=/usr/local/cdo/1.9.3_gcc85/bin/cdo
cd /data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM/tmp || exit 1
$NCKS -O --mk_rec_dmn time 1980_era5.nc rec.nc
for v in TBOT PRECTmms FLDS WIND QBOT; do
  $CDO -s selname,$v -monmean rec.nc "${v}_mon_1980.nc"
  echo "$v: $($CDO -s ntime ${v}_mon_1980.nc) months"
done
rm -f rec.nc
echo "DONE"
