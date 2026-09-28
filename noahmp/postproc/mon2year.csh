#!/bin/tcsh -f
#==============================================================================
#  mon2year.csh -- Noah-MP monthly post-processed files -> one file per year
#
#  in   postproc/noahmp_prod_mon_YYYYMM.nc   (12 per year, from
#                                             ldasout_6h_to_daymon.py)
#  out  postproc/yearly/noahmp_prod.YYYY.nc  (12 records)
#
#  ISNOW is dropped: it is integer-typed, so the 6h->monthly step froze it at
#  the month's first snapshot instead of averaging (it really does vary in
#  time, -3..0).  Snow physics is carried by SNOWH / SNEQV / FSNO; if the layer
#  count is ever needed it is in the 6h raw.  IVGTYP / ISLTYP are genuinely
#  static and are kept.
#
#  ncrcat verified against python for 1979: 97 of 98 variables bit-identical,
#  masks identical, attributes and _FillValue preserved (notes 12).
#
#  usage:  tcsh mon2year.csh [Y0 Y1]
#==============================================================================

set NCO = /usr/local/nco/4.8.0_gcc85/bin
setenv LD_LIBRARY_PATH ${NCO}/lib:/usr/local/netcdf/4.6.1_gcc85/lib:/usr/local/udunits/2.1.24_gcc85/lib

set P = /home/ydkoh/HRLDAS/forcing_WFDE5_1deg/prod_1979_2023/postproc
set OUT = $P/yearly

set Y0 = 1979
set Y1 = 2023
if ($#argv == 2) then
  set Y0 = $1
  set Y1 = $2
endif

mkdir -p $OUT

@ YEAR = $Y0
while ($YEAR <= $Y1)
  set n = `ls $P/noahmp_prod_mon_${YEAR}??.nc | wc -l`
  if ($n != 12) then
    echo "ABORT: $YEAR has $n monthly files, expected 12"
    exit 1
  endif
  ${NCO}/ncrcat -O -x -v ISNOW $P/noahmp_prod_mon_${YEAR}??.nc $OUT/noahmp_prod.${YEAR}.nc
  if ($status != 0) then
    echo "ABORT: ncrcat failed for $YEAR"
    exit 1
  endif
  echo "$YEAR done"
  @ YEAR ++
end

echo "ALL DONE $Y0-$Y1 `date`"
