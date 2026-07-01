#!/bin/bash
# cycle5(2876) 완료 후 → 복구 cycle2,3 (Global 30-89) 순차 → 메인 spin-up 재개(cycle6+ →300).
# 전부 raw 보존(spinup_raw/yN). 어느 단계든 exit!=0면 중단.
set -u
source /home/ydkoh/anaconda3/etc/profile.d/conda.sh; conda activate
LM4=/data2/ydkoh/lm4
RD=$LM4/RUN/lm4_spinup
PBS=spinup24.pbs
log(){ echo "[$(date '+%m-%d %H:%M')] $*"; }
wait_for(){ while qstat "$1" >/dev/null 2>&1; do sleep 300; done; }
fdate(){ ls "$RD/RESTART/" 2>/dev/null | grep -oE '^[0-9]{8}\.[0-9]{6}' | sort -u | tail -1; }
preserve(){ local R=$LM4/spinup_raw/y$1; mkdir -p "$R"
  cp "$RD/RESTART/"*.res* "$R/" 2>/dev/null
  cp "$RD/19810101.land_annual.tile"*.nc "$R/" 2>/dev/null
  local c=$(ls -t "$RD/"ufs.cpld.cpl.hi.lnd.*.nc 2>/dev/null|head -1); [ -n "$c" ] && cp "$c" "$R/coords.cpl.hi.lnd.nc"; }
stage(){ rm -f "$RD/INPUT/"*.res.tile*.nc "$RD/INPUT/landuse.res"
  for f in "$@"; do cp "$f" "$RD/INPUT/$(basename "$f"|sed -E 's/^[0-9]{8}\.[0-9]{6}\.//')"; done
  grep -q "start_type = continue" "$RD/ufs.configure" || sed -i "s/start_type = startup/start_type = continue/" "$RD/ufs.configure"; }
regional(){ python "$LM4/lm4_region_spinup.py" --rundir "$RD" --base_year "$1" --csv "$LM4/region_spinup.csv" --png "$LM4/region_spinup.png" 2>&1|tail -1; }
runcyc(){ rm -f "$RD/RESTART/"* "$RD"/ufs.cpld.cpl.hi.lnd.*
  local J=$(cd "$LM4" && qsub "$PBS"|grep -oE '^[0-9]+'); log "  job $J 제출"; wait_for "$J"; sleep 15
  tail -3 "$RD/spinup.log"|grep -q "END exit=0" || { log "  ★FAIL job $J"; exit 1; }; }

log "=== 복구+재개 시작: cycle5(2876) 대기 ==="
wait_for 2876; sleep 15
tail -3 "$RD/spinup.log"|grep -q "END exit=0" || { log "★cycle5 FAIL, 중단"; exit 1; }
D=$(fdate); preserve 150
mkdir -p $LM4/IC_static_150yr; rm -f $LM4/IC_static_150yr/*; cp "$RD/RESTART/$D".* $LM4/IC_static_150yr/
regional 120; log "cycle5 처리완료(150yr), raw y150 보존"

log "=== 복구 cycle2 (year-30 IC → Global 31-59) ==="
stage $LM4/IC_GSWP3_staticveg_spin30/*.res*
runcyc
D=$(fdate); preserve 60; regional 30
log "복구 cycle2 완료 → Global 31-59 채움, raw y60"

log "=== 복구 cycle3 (→ Global 61-89) ==="
stage "$RD/RESTART/$D".*.res*
runcyc
D=$(fdate); preserve 90; regional 60
log "복구 cycle3 완료 → Global 61-89 채움, raw y90"

log "=== 메인 spin-up 재개 (year-150 → cycle6+ → 300) ==="
stage $LM4/IC_static_150yr/*.res*
rm -f "$RD/RESTART/"* "$RD"/ufs.cpld.cpl.hi.lnd.*
J6=$(cd $LM4 && qsub $PBS|grep -oE '^[0-9]+')
nohup bash $LM4/spinup_loop.sh $J6 180 300 >& $LM4/spinup_loop.log &
log "=== 완료: 메인 재개 cycle6=job $J6 (180→300). Global 1-89 채워짐 ==="
