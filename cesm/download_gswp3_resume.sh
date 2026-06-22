#!/bin/bash
# GSWP3 0.5deg datm forcing: diagnose missing files and (optionally) download
# the missing ones from the UCAR CESM inputdata server. Resume-safe per-file wget.
#   usage:  bash download_gswp3_resume.sh diagnose      # count missing only
#           bash download_gswp3_resume.sh download      # fetch missing files
#   env:    Y0, Y1 override the year range (default 1979-2014)
set -u
D=/data1/CESM2_INPUT/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v1.c170516
BASE=https://svn-ccsm-inputdata.cgd.ucar.edu/trunk/inputdata/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v1.c170516
Y0=${Y0:-1979}; Y1=${Y1:-2014}
LOG=/data2/ydkoh/gswp3_resume.log
MODE=${1:-diagnose}                       # diagnose | download
subs=("Precip Prec" "Solar Solr" "TPHWL TPQWL")

cd "$D" || { echo "no dir $D"; exit 1; }
[ "$MODE" = "download" ] && echo "==== GSWP3 download START $(date '+%F %T')  yrs $Y0-$Y1 ====" >> "$LOG"

per=$(( (Y1 - Y0 + 1) * 12 ))
total_miss=0
for st in "${subs[@]}"; do
  set -- $st; sub=$1; tag=$2
  miss=0
  for y in $(seq "$Y0" "$Y1"); do
    for m in $(seq -w 1 12); do
      f="$sub/clmforc.GSWP3.c2011.0.5x0.5.$tag.$y-$m.nc"
      if [ ! -s "$f" ]; then
        miss=$((miss + 1)); total_miss=$((total_miss + 1))
        if [ "$MODE" = "download" ]; then
          if wget --no-check-certificate -c -q -O "$f" "$BASE/$sub/$(basename "$f")"; then
            echo "OK   $f" >> "$LOG"
          else
            echo "FAIL $f" >> "$LOG"; rm -f "$f"   # drop partial/failed so it retries next round
          fi
        fi
      fi
    done
  done
  echo "$sub: missing $miss / $per"
done
echo "TOTAL missing $total_miss"
echo "svn temp leftovers: $(ls */svn-* 2>/dev/null | wc -l)"
[ "$MODE" = "download" ] && echo "==== GSWP3 download END $(date '+%F %T')  still_missing scan above ====" >> "$LOG"
