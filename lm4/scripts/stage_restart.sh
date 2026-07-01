#!/bin/bash
# 아카이브 30년 land restart를 FMS 규약(날짜 없는 이름)으로 INPUT/에 스테이징
ic=/data2/ydkoh/lm4/IC_GSWP3_staticveg_spin30
d=/data2/ydkoh/lm4/RUN/lm4_spinup
rm -f "$d/INPUT/"19810101.000000.*.res* "$d/INPUT/"*.res.tile*.nc "$d/INPUT/landuse.res 2>/dev/null"
rm -f "$d/INPUT/"*.res.tile*.nc 2>/dev/null
n=0
for f in "$ic"/20100101.000000.*; do
  # 날짜.시각. prefix 제거 → soil.res.tile1.nc 식
  b=$(basename "$f" | sed -E 's/^[0-9]{8}\.[0-9]{6}\.//')
  cp "$f" "$d/INPUT/$b" && n=$((n+1))
done
echo "staged $n files (undated):"
ls "$d/INPUT/"*.res* 2>/dev/null | xargs -n1 basename | sed -E 's/\.tile[0-9]//' | sort -u
