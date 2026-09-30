#!/bin/bash
# Fill missing WFDE5 1-deg forcing with nearest-neighbour values (cdo setmisstonn).
#
# Why: the JULES 1-deg land mask comes from the 0.5 deg ancil (notes 13), not
# from WFDE5, and the two disagree on coasts and islands.  406 of the 17,295
# JULES land cells get _FillValue forcing from the CDO remap (98 of them are
# partial-coast cells CDO masks, 308 have no WFDE5 data at all).  JULES does
# not check forcing for missing values, so these cells would run on 1e20.
#
# Checked on 1981 (notes 15): missing after fill 0, originally valid values
# unchanged (max|diff| 0), 1460 records.  326 gap cells take values from <= 1
# deg away; 80 remote islands take them from 1-41 deg away (e.g. French
# Polynesia <- Fiji) and are listed in jules_wfde5_gapcells_1deg.nc so the
# analysis can exclude them.
#
# setmisstonn is slow (~25 min/yr, it searches neighbours every time step),
# so years run NPAR at a time.  CDO only, so it may run on climate00.
# usage: nohup bash wfde5_nnfill_1deg.sh >& nnfill.log &

CDO=/usr/local/cdo/1.9.3_gcc85/bin/cdo
export LD_LIBRARY_PATH=/usr/local/netcdf/4.6.1_gcc85/lib:/usr/local/hdf5/1.10.5_gcc85/lib:$LD_LIBRARY_PATH
I=/data2/ydkoh/jules_wfde5_1deg
O=/data2/ydkoh/jules_wfde5_1deg_nnfill
mkdir -p $O

Y0=${Y0:-1979}
Y1=${Y1:-2023}
NPAR=${NPAR:-8}

fill_year() {
  local yr=$1
  local out=$O/wfde5_1deg_${yr}.nc
  # Write to .tmp and rename only on success, so a killed run leaves nothing
  # that passes the -s test below.
  rm -f $out.tmp
  if $CDO -s setmisstonn $I/wfde5_1deg_${yr}.nc $out.tmp; then
    mv -f $out.tmp $out
    echo "  $yr done $(date +%H:%M)"
  else
    echo "FAILED $yr"
    rm -f $out.tmp
  fi
}

echo "=== WFDE5 1 deg nearest-neighbour fill ($Y0-$Y1, NPAR=$NPAR) START $(date) ==="
for yr in $(seq $Y0 $Y1); do
  out=$O/wfde5_1deg_${yr}.nc
  if [ -s "$out" ]; then echo "  $yr already done"; continue; fi
  while [ $(jobs -rp | wc -l) -ge $NPAR ]; do wait -n; done
  fill_year $yr &
done
wait
echo "=== END $(ls $O/*.nc | wc -l) files (expect $((Y1-Y0+1))) $(date) ==="
