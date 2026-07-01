#!/bin/bash
# 무인 continue 스핀업 오케스트레이터 (static veg, leap, clamp).
# 각 cycle = 30년 continue (forcing 1981-2010 replay, land 상태 누적, 시계 1981 리셋).
# cycle마다: 완주확인 → 아카이빙 → continue 스테이징(무날짜) → 다음 제출 → ★warm-start 검증(cold면 중단).
#
# 사용 (서버, nohup): nohup bash spinup_loop.sh <CUR_JOBID> <YEARS_AFTER_CUR> <TARGET> >& spinup_loop.log &
#   예) 2871이 60년까지 가는 중, 300년 목표:
#       nohup bash spinup_loop.sh 2871 60 300 >& /data2/ydkoh/lm4/spinup_loop.log &
set -u
source /home/ydkoh/anaconda3/etc/profile.d/conda.sh; conda activate
LM4=/data2/ydkoh/lm4
RUNDIR=$LM4/RUN/lm4_spinup
PBS=spinup24.pbs
CUR=${1:?need running jobid}
YEARS=${2:?need years-after-cur}
TARGET=${3:-300}

log(){ echo "[$(date '+%m-%d %H:%M')] $*"; }
wait_for(){ while qstat "$1" >/dev/null 2>&1; do sleep 300; done; }
final_date(){ ls "$RUNDIR/RESTART/" 2>/dev/null | grep -oE '^[0-9]{8}\.[0-9]{6}' | sort -u | tail -1; }

log "=== orchestrator 시작: CUR=$CUR, 현재 ${YEARS}yr, 목표 ${TARGET}yr ==="
while true; do
  log "job $CUR 대기 (완주 시 ${YEARS}yr) ..."
  wait_for "$CUR"; sleep 15
  if ! tail -3 "$RUNDIR/spinup.log" | grep -q "END exit=0"; then
    log "★중단: job $CUR 가 exit=0 아님 (크래시). spinup.log 확인 요망."; exit 1
  fi
  D=$(final_date)
  # ★ raw 전체 보존 (절대 안 지움) — 모든 연간 restart + land_annual + 좌표용 cpl.hi 1개
  RAW=$LM4/spinup_raw/y${YEARS}; mkdir -p "$RAW"
  cp "$RUNDIR/RESTART/"*.res* "$RAW/" 2>/dev/null
  cp "$RUNDIR/19810101.land_annual.tile"*.nc "$RAW/" 2>/dev/null
  cf=$(ls -t "$RUNDIR/"ufs.cpld.cpl.hi.lnd.*.nc 2>/dev/null | head -1); [ -n "$cf" ] && cp "$cf" "$RAW/coords.cpl.hi.lnd.nc"
  IC=$LM4/IC_static_${YEARS}yr; mkdir -p "$IC"; rm -f "$IC"/*; cp "$RUNDIR/RESTART/$D".* "$IC/"
  log "cycle 완주 @ ${YEARS}yr → raw 전체 보존 $RAW + IC $IC"

  # --- 지역별 spin-up 추적 그림 갱신 (누적연수 라벨) ---
  python "$LM4/lm4_region_spinup.py" --rundir "$RUNDIR" --base_year $((YEARS-30)) \
      --csv "$LM4/region_spinup.csv" --png "$LM4/region_spinup.png" 2>&1 | tail -1
  log "지역 spin-up 그림 갱신 → region_spinup.png (~${YEARS}yr)"

  if [ "$YEARS" -ge "$TARGET" ]; then log "=== ★목표 ${TARGET}yr 도달. 종료. (평형검증: python lm4_equil2.py) ==="; break; fi

  # --- continue 스테이징 (무날짜 FMS 이름) ---
  rm -f "$RUNDIR/INPUT/"*.res.tile*.nc "$RUNDIR/INPUT/landuse.res"
  for f in "$RUNDIR/RESTART/$D".*.res*; do
    cp "$f" "$RUNDIR/INPUT/$(basename "$f" | sed -E 's/^[0-9]{8}\.[0-9]{6}\.//')"
  done
  grep -q "start_type = continue" "$RUNDIR/ufs.configure" || \
    sed -i "s/start_type = startup/start_type = continue/" "$RUNDIR/ufs.configure"
  rm -f "$RUNDIR/RESTART/"* "$RUNDIR"/ufs.cpld.cpl.hi.lnd.*

  # --- 다음 cycle 제출 ---
  CUR=$(cd "$LM4" && qsub "$PBS" | grep -oE '^[0-9]+'); YEARS=$((YEARS+30))
  log "다음 cycle 제출: job $CUR (완주 시 ${YEARS}yr)"

  # --- ★warm-start 검증 (첫 해 restart deep soil T) ---
  for t in $(seq 1 15); do
    sleep 120
    ls "$RUNDIR/RESTART/"19820101.000000.soil.res.tile1.nc >/dev/null 2>&1 && break
  done
  DT=$(python "$LM4/check_warm.py" 2>/dev/null | grep -oE '[0-9]+\.[0-9]+ K' | grep -oE '^[0-9]+\.[0-9]+')
  log "  warm-start 검증: 첫해 deep soil T = ${DT:-?}K"
  if [ -n "${DT:-}" ] && awk "BEGIN{exit !($DT>285)}"; then
    log "★중단: cold-start로 떨어짐 (deep T=${DT}K, warm이면 <280). 스테이징 확인 요망."
    qdel "$CUR" 2>/dev/null; exit 1
  fi
done
