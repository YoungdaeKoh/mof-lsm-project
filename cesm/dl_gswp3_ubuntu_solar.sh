#!/bin/bash
# GSWP3 Solar (1901-2014, monthly) -> ubuntu /mnt/data2. UCAR https, resume-safe.
# Part of 3-machine split: server=Precip, ubuntu=Solar, mac=TPHWL.
BASE=https://svn-ccsm-inputdata.cgd.ucar.edu/trunk/inputdata/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v1.c170516/Solar
DEST=/mnt/data2/GSWP3_ERA5testbed/Solar
LOG=/mnt/data2/gswp3_solar.log
mkdir -p "$DEST"; cd "$DEST" || exit 1
echo "==== Solar START $(date '+%F %T') ====" >> "$LOG"
for y in $(seq 1901 2014); do
  for m in 01 02 03 04 05 06 07 08 09 10 11 12; do
    f=clmforc.GSWP3.c2011.0.5x0.5.Solr.${y}-${m}.nc
    if wget --no-check-certificate -c -q "$BASE/$f"; then :; else echo "FAIL $f" >> "$LOG"; fi
  done
  echo "year $y done $(date '+%T')  have=$(ls *.nc 2>/dev/null | wc -l)/1368" >> "$LOG"
done
echo "==== Solar DONE $(date '+%F %T')  files=$(ls *.nc 2>/dev/null | wc -l) ====" >> "$LOG"
