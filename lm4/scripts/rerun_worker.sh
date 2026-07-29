#!/bin/bash
# Re-run selected LM4 years so that December's monthly record exists.
#
# Why: the production chain uses days=364/hours=21, which ends at Jan 1 00:00.
# The monthly averaging windows are anchored to the run start (03:00), so
# December's window runs Dec 1 03:00 -> Jan 1 03:00 and never completes; every
# year therefore holds 11 land_month records. Adding 3 hours closes it.
#
# Each year is independent: it starts from the archived restart written at the
# end of year Y-1, so these runs reproduce the original trajectory exactly and
# only add the missing December. They do NOT chain into each other.
#
# usage: rerun_worker.sh <workerdir> <year> [year ...]
set -u
R=$1; shift
SRC=/data2/ydkoh/lm4/RUN/lm4_spinup30
log() { echo "[$(date '+%F %T')] $*" | tee -a "$R/rerun.chain.log"; }

for Y in "$@"; do
  P=$((Y - 1))
  if [ ! -d "$SRC/archive/y$P" ]; then
    log "ABORT: no archived restart for y$P (needed to start y$Y)"; exit 1
  fi

  # The worker MUST own its FORCING directory. The production chain re-points
  # $R/FORCING/wfde5_atm.nc to the year it is currently running
  # (chain_spinup30.sh:37), so sharing that directory hands the worker the wrong
  # year - the first attempt died with
  #   "time 19900101.033000 is before range 19960101.030000-19970101.090000".
  FY=/data2/ydkoh/lm4/forcing_WFDE5_lm4p/wfde5_atm_${Y}.nc
  [ -s "$FY" ] || { log "ABORT: forcing missing $FY"; exit 1; }
  mkdir -p "$R/FORCING"
  ln -sfn "$FY" "$R/FORCING/wfde5_atm.nc"
  log "y$Y: forcing -> $(readlink "$R/FORCING/wfde5_atm.nc")"

  log "y$Y: staging restart from archive/y$P"
  rm -f "$R"/INPUT/*.res*.nc "$R"/INPUT/*.res*.nc.0*
  cp -p "$SRC/archive/y$P"/*.res* "$R/INPUT"/ || { log "ABORT: restart copy failed"; exit 1; }

  # 365d 0h ends at Jan 1 03:00 of the next year, closing December's window.
  # The calendar is NOLEAP (coupler_nml), so every year is 365 days - no leap
  # branch is needed. Forcing runs to day 365.375, giving 9 h of headroom.
  sed -e "s/^        days   = .*/        days   = 365,/" \
      -e "s/^        hours  = .*/        hours  = 0,/" \
      -e "s/^        current_date = .*/        current_date = ${Y},1,1,3,0,0,/" \
      "$SRC/input.nml.template" > "$R/input.nml"

  rm -f "$R"/esm4p5.log "$R"/*.nc.0* "$R"/*.nc
  rm -rf "$R/RESTART"; mkdir -p "$R/RESTART"

  JID=$(qsub "$R/run_rerun.sh")
  [ -n "$JID" ] || { log "ABORT: qsub returned nothing for y$Y"; exit 1; }
  log "y$Y job $JID submitted"
  while qstat "$JID" >/dev/null 2>&1; do sleep 120; done

  if grep -q 'FATAL' "$R/esm4p5.log" 2>/dev/null && \
     grep 'FATAL' "$R/esm4p5.log" | grep -qv FATAL_UNUSED_PARAMS; then
    log "ABORT: FATAL in y$Y"
    grep 'FATAL' "$R/esm4p5.log" | grep -v FATAL_UNUSED_PARAMS | head -3 | tee -a "$R/rerun.chain.log"
    exit 1
  fi

  # the whole point of the exercise: 12 monthly records, not 11
  n=$(ls "$R"/*.land_month.tile1.nc 2>/dev/null | head -1)
  if [ -n "$n" ]; then
    nm=$(ncdump -h "$n" | grep -m1 'time = UNLIMITED' | grep -oE '\([0-9]+ currently' | grep -oE '[0-9]+')
    log "y$Y land_month records = ${nm:-?}"
    [ "${nm:-0}" -ge 12 ] || log "WARNING: y$Y still has ${nm:-?} records, expected 12"
  else
    log "ABORT: y$Y produced no land_month output"; exit 1
  fi

  mkdir -p "$R/archive/y$Y"
  mv "$R"/*.land_*.nc "$R/archive/y$Y"/ 2>/dev/null
  cp -p "$R/RESTART"/*.res* "$R/archive/y$Y"/ 2>/dev/null
  log "y$Y archived: $(ls "$R/archive/y$Y" | wc -l) files"
done
log "worker complete: $*"
