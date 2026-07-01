#!/bin/bash
# climate02 + backfill dir에서 복구 cycle2,3 (Global 31-89). 메인(climate01)과 완전 분리.
set -u
source /home/ydkoh/anaconda3/etc/profile.d/conda.sh; conda activate
LM4=/data2/ydkoh/lm4; RD=$LM4/RUN/lm4_backfill; PBS=backfill_c02.pbs; CSV=$LM4/region_recov.csv
log(){ echo "[$(date '+%m-%d %H:%M')] $*"; }
wait_for(){ while qstat "$1" >/dev/null 2>&1; do sleep 300; done; }
fdate(){ ls "$RD/RESTART/" 2>/dev/null | grep -oE '^[0-9]{8}\.[0-9]{6}' | sort -u | tail -1; }
preserve(){ local R=$LM4/spinup_raw/$1; mkdir -p "$R"
  cp "$RD/RESTART/"*.res* "$R/" 2>/dev/null
  cp "$RD/19810101.land_annual.tile"*.nc "$R/" 2>/dev/null
  local c=$(ls -t "$RD/"ufs.cpld.cpl.hi.lnd.*.nc 2>/dev/null|head -1); [ -n "$c" ] && cp "$c" "$R/coords.cpl.hi.lnd.nc"; }
stage(){ rm -f "$RD/INPUT/"*.res.tile*.nc "$RD/INPUT/landuse.res"
  for f in "$@"; do cp "$f" "$RD/INPUT/$(basename "$f"|sed -E 's/^[0-9]{8}\.[0-9]{6}\.//')"; done
  grep -q "start_type = continue" "$RD/ufs.configure" || sed -i "s/start_type = startup/start_type = continue/" "$RD/ufs.configure"; }
regional(){ python "$LM4/lm4_region_spinup.py" --rundir "$RD" --base_year "$1" --csv "$CSV" --png "$LM4/region_recov.png" 2>&1|tail -1; }
runcyc(){ rm -f "$RD/RESTART/"* "$RD"/ufs.cpld.cpl.hi.lnd.*
  local J=$(cd "$LM4" && qsub "$PBS"|grep -oE '^[0-9]+'); log "  job $J 제출(climate02)"; wait_for "$J"; sleep 15
  tail -3 "$RD/spinup.log"|grep -q "END exit=0" || { log "  ★FAIL job $J"; exit 1; }; }
log "=== climate02 복구: cycle2 (year-30 IC → Global 31-59) ==="
stage $LM4/IC_GSWP3_staticveg_spin30/*.res*
runcyc; D=$(fdate); preserve y60recov; regional 30
log "복구 cycle2 완료 → Global 31-59"
log "=== 복구 cycle3 (→ Global 61-89) ==="
stage "$RD/RESTART/$D".*.res*
runcyc; D=$(fdate); preserve y90recov; regional 60
log "=== 복구 완료: Global 31-89 → region_recov.csv (메인에 병합 대기) ==="
