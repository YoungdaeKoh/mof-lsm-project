#!/bin/bash
G=/data1/CESM2_INPUT/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v1.c170516
ND=/usr/local/netcdf/4.6.1_gcc85/bin/ncdump
echo "===== TPQWL 데이터 변수 (좌표 제외) ====="
$ND -h $(ls "$G/TPHWL"/*.nc | head -1) 2>/dev/null | grep -E "float [A-Z].*\(time" | head
echo "===== 습도 변수 상세 (specific humidity?) ====="
$ND -h $(ls "$G/TPHWL"/*.nc | head -1) 2>/dev/null | grep -iA3 "QBOT\|SHUM\|Qair" | head -8
echo "===== 심링크 팜 생성 (1981-2010, 3그룹 flat) ====="
FARM=/data2/ydkoh/jules_gswp3_forcing
mkdir -p "$FARM"
n=0
for s in Precip Solar TPHWL; do
  for y in $(seq 1981 2010); do
    for f in "$G/$s"/clmforc.GSWP3.c2011.0.5x0.5.*.${y}-*.nc; do
      [ -e "$f" ] && ln -sf "$f" "$FARM/$(basename "$f")" && n=$((n+1))
    done
  done
done
echo "심링크 $n 개 생성 → $FARM"
echo "===== 샘플 확인 ====="
ls "$FARM" | head -3
ls "$FARM" | grep -c "1981-01"
echo "domain 파일도 링크:"
ln -sf "$G/domain.lnd.360x720_gswp3.0v1.c170606.nc" "$FARM/" && ls "$FARM"/domain* 2>/dev/null
