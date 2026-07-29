#!/bin/bash
# Drive the 30-year offline lm4P spin-up, one model year per PBS job.
#
# v2 (2026-07-29): segment length 364d21h -> 365d0h so that December's
# monthly record is actually written. See the comment at the sed below.
#
# Guards exist because a previous auto-chain crash-looped ~5000 times: the date
# it parsed came back empty, the "did it finish" test passed on a stale restart,
# and it resubmitted forever. So here: progress is judged by the restart being
# strictly newer than the one we started from, anything unparsed aborts, and a
# hard counter caps the whole run.
#
# Raw output is never deleted -- each year's restarts and land history are
# archived before the run directory is reused (see lsm-spinup-raw-preservation).
set -u

R=/data2/ydkoh/lm4/RUN/lm4_spinup30
F=/data2/ydkoh/lm4/forcing_WFDE5_lm4p
Y0=${1:-1981}
Y1=${2:-2010}
MAXSEG=35                       # hard cap: 30 years + slack

cd "$R"
log() { echo "[$(date +%F\ %T)] $*" | tee -a "$R/chain.log"; }

seg=0
for Y in $(seq "$Y0" "$Y1"); do
  seg=$((seg + 1))
  if [ "$seg" -gt "$MAXSEG" ]; then
    log "ABORT: segment cap $MAXSEG reached"; exit 1
  fi

  if [ -d "$R/archive/y$Y" ]; then
    log "y$Y already archived, skipping"
    continue
  fi

  FY="$F/wfde5_atm_${Y}.nc"
  [ -s "$FY" ] || { log "ABORT: forcing missing $FY"; exit 1; }
  ln -sfn "$FY" "$R/FORCING/wfde5_atm.nc"

  # WFDE5 records sit at 03/09/15/21 UTC (6-hour interval centres), so a segment
  # can only start at 03:00 -- which also anchors every monthly averaging window
  # to 03:00. December's window is therefore Dec 1 03:00 -> Jan 1 03:00.
  #
  # The previous setting (364 d 21 h) ended at Jan 1 00:00, three hours short of
  # that, so December's average never completed and every year wrote only 11
  # land_month records. The old comment here claimed it wrote 12; it did not.
  # Verified on 1981-1995: 11 records in all fifteen years.
  #
  # 365 d 0 h ends at Jan 1 03:00, closing December, and the next segment starts
  # at exactly that instant, so the 3 h gap at each year break also disappears.
  # The calendar is NOLEAP (coupler_nml), so every year is 365 days and no leap
  # branch is needed. Forcing runs to day 365.375, leaving 9 h of headroom.
  sed -e "s/^        days   = .*/        days   = 365,/" \
      -e "s/^        hours  = .*/        hours  = 0,/" \
      -e "s/^        current_date = .*/        current_date = ${Y},1,1,3,0,0,/" \
      "$R/input.nml.template" > "$R/input.nml"

  # Baseline for the progress test: restart mtime we are starting from.
  # 24 PE writes a combined cana.res.tile1.nc; fall back to the .0001 piece so
  # the guard still works if a run ever produces distributed restarts.
  before=$(stat -c %Y "$R/INPUT/cana.res.tile1.nc" 2>/dev/null \
           || stat -c %Y "$R/INPUT/cana.res.tile1.nc.0001" 2>/dev/null || echo 0)

  rm -f "$R"/esm4p5.log "$R"/*.nc.0* "$R"/*.nc
  rm -rf "$R/RESTART"; mkdir -p "$R/RESTART"

  log "y$Y segment $seg: submitting"
  JID=$(qsub "$R/run_spinup30.sh")
  [ -n "$JID" ] || { log "ABORT: qsub returned nothing for y$Y"; exit 1; }
  log "y$Y job $JID"

  while qstat "$JID" >/dev/null 2>&1; do sleep 120; done

  # --- guard 1: the model must not have aborted -------------------------------
  if grep -q 'FATAL' "$R/esm4p5.log" 2>/dev/null && \
     grep 'FATAL' "$R/esm4p5.log" | grep -qv FATAL_UNUSED_PARAMS; then
    log "ABORT: FATAL in y$Y"
    grep 'FATAL' "$R/esm4p5.log" | grep -v FATAL_UNUSED_PARAMS | head -3 | tee -a "$R/chain.log"
    exit 1
  fi

  # --- guard 2: a complete restart set must exist ------------------------------
  n=$(ls "$R/RESTART"/*.res*.nc 2>/dev/null | wc -l)
  if [ "$n" -lt 40 ]; then
    log "ABORT: y$Y wrote only $n restart files (expected >=40)"; exit 1
  fi

  # --- guard 3: it must be NEWER than what we started from ---------------------
  after=$(stat -c %Y "$R/RESTART/cana.res.tile1.nc" 2>/dev/null \
          || stat -c %Y "$R/RESTART/cana.res.tile1.nc.0001" 2>/dev/null || echo 0)
  if [ "$after" -le "$before" ]; then
    log "ABORT: y$Y restart not newer than input (stale restart -> would loop)"; exit 1
  fi

  # --- archive raw before reusing the run directory ----------------------------
  mkdir -p "$R/archive/y$Y"
  cp -p "$R/RESTART"/*.res* "$R/archive/y$Y"/ 2>/dev/null
  mv "$R"/*.land_*.nc "$R/archive/y$Y"/ 2>/dev/null
  log "y$Y archived: $(ls "$R/archive/y$Y" | wc -l) files"

  # --- hand the restart to the next segment ------------------------------------
  cp -p "$R/RESTART"/*.res* "$R/INPUT"/
  log "y$Y done"
done

log "chain complete: $Y0-$Y1"
