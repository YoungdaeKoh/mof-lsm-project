#!/bin/bash
# Drive lm4p_ctl_1979-2024, the production run: 46 transient years, one model
# year per PBS job, 48 PE.
#
# Derived from chain_spinup30_v2.sh, which drove cycle 1.  That script is left
# as the record of how the initial state was reached; the differences here are:
#
#   * its own directory, so cycle 1 (now archive_c1) cannot be written over
#   * 48 PE with npes_io_group=48 -- combined output, verified in job 8365.
#     At npes_io_group=8 the land writes .0001/.0002 pieces that the archive
#     pattern below does not match and the next segment's rm does (13.48)
#   * guard 4: a year must carry twelve monthly records.  1981-1996 wrote
#     eleven for fifteen years before anyone noticed (13.31); the check costs
#     one ncdump and makes that failure impossible to accumulate
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

R=${R:-/data2/ydkoh/lm4/RUN/lm4p_ctl_1979-2024}   # override for a variant run (e.g. lm4p_lufix_1979-2023)
F=/data2/ydkoh/lm4/forcing_WFDE5_lm4p
Y0=${1:-1979}
Y1=${2:-2024}
MAXSEG=50                       # hard cap: 46 years + slack

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
  # 365 d 0 h ends at Jan 1 03:00, closing December, and the next segment starts
  # at exactly that instant, so there is no gap at the year break.  The calendar
  # is NOLEAP (coupler_nml), so every year is 365 days.  Each forcing file was
  # given the next year's first two records (day 365.125, 365.375) so the last
  # timestep is inside the file's range -- see append_boundary_1979_2024.py.
  sed -e "s/^        days   = .*/        days   = 365,/" \
      -e "s/^        hours  = .*/        hours  = 0,/" \
      -e "s/^        current_date = .*/        current_date = ${Y},1,1,3,0,0,/" \
      "$R/input.nml.template" > "$R/input.nml"

  # Baseline for the progress test: restart mtime we are starting from.
  before=$(stat -c %Y "$R/INPUT/cana.res.tile1.nc" 2>/dev/null || echo 0)

  rm -f "$R"/esm4p5.log "$R"/*.nc.0* "$R"/*.nc
  rm -rf "$R/RESTART"; mkdir -p "$R/RESTART"

  log "y$Y segment $seg: submitting"
  JID=$(qsub "$R/run_lm4p_ctl.sh")
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
  after=$(stat -c %Y "$R/RESTART/cana.res.tile1.nc" 2>/dev/null || echo 0)
  if [ "$after" -le "$before" ]; then
    log "ABORT: y$Y restart not newer than input (stale restart -> would loop)"; exit 1
  fi

  # --- guard 4: twelve monthly records, and six combined tiles ----------------
  # Catches both failures that have actually happened: a segment three hours
  # short of closing December, and an io layout that splits the land output.
  ntile=$(ls "$R"/${Y}0101.land_month.tile?.nc 2>/dev/null | wc -l)
  if [ "$ntile" -ne 6 ]; then
    log "ABORT: y$Y wrote $ntile combined land_month tiles, expected 6"
    log "       (pieces present: $(ls "$R"/${Y}0101.land_month.tile?.nc.[0-9][0-9][0-9][0-9] 2>/dev/null | wc -l) -- check npes_io_group)"
    exit 1
  fi
  nrec=$(ncdump -h "$R/${Y}0101.land_month.tile1.nc" \
         | sed -n 's/.*time = UNLIMITED.*(\([0-9]*\) currently.*/\1/p')
  if [ "$nrec" != "12" ]; then
    log "ABORT: y$Y wrote $nrec land_month records, expected 12"; exit 1
  fi

  # --- archive raw before reusing the run directory ----------------------------
  mkdir -p "$R/archive/y$Y"
  cp -p "$R/RESTART"/*.res* "$R/archive/y$Y"/ 2>/dev/null
  # river_* as well as land_*: matching only land_* is how 1997-2009 of cycle 1
  # lost their routed discharge to the next segment's rm.  Anything not moved
  # here does not survive.
  mv "$R"/*.land_*.nc "$R"/*.river_*.nc "$R/archive/y$Y"/ 2>/dev/null
  log "y$Y archived: $(ls "$R/archive/y$Y" | wc -l) files, ${nrec} monthly records"

  # --- hand the restart to the next segment ------------------------------------
  cp -p "$R/RESTART"/*.res* "$R/INPUT"/
  log "y$Y done"
done

log "chain complete: $Y0-$Y1"
