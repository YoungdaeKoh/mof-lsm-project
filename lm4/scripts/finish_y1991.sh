#!/bin/bash
# Archive the 1991 re-run after its PBS job ends.
#
# The worker driver was stopped so that no further year would be submitted, but
# the worker is also what archives each year. Without this, 1991's output would
# be left loose in the run directory and the next worker launch would delete it
# (the worker does `rm -f $R/*.nc` before每 year).
set -u
R=/data2/ydkoh/lm4/RERUN/wA
JID=${1:-8332.climate00}
Y=1991
log() { echo "[$(date +%F\ %T)] finish: $*" | tee -a "$R/rerun.chain.log"; }

log "waiting for $JID (y$Y)"
while qstat "$JID" >/dev/null 2>&1; do sleep 120; done
log "$JID finished"

if grep -q 'FATAL' "$R/esm4p5.log" 2>/dev/null && \
   grep 'FATAL' "$R/esm4p5.log" | grep -qv FATAL_UNUSED_PARAMS; then
  log "ABORT: FATAL in y$Y - leaving output in place for inspection"; exit 1
fi

f=$(ls "$R"/*.land_month.tile1.nc 2>/dev/null | head -1)
if [ -n "$f" ]; then
  nm=$(ncdump -h "$f" | grep -m1 'time = UNLIMITED' | grep -oE '\([0-9]+ currently' | grep -oE '[0-9]+')
  log "y$Y land_month records = ${nm:-?}"
  [ "${nm:-0}" -ge 12 ] || log "WARNING: y$Y has ${nm:-?} records, expected 12"
else
  log "ABORT: y$Y produced no land_month output"; exit 1
fi

mkdir -p "$R/archive/y$Y"
mv "$R"/*.land_*.nc "$R/archive/y$Y"/ 2>/dev/null
cp -p "$R/RESTART"/*.res* "$R/archive/y$Y"/ 2>/dev/null
log "y$Y archived: $(ls "$R/archive/y$Y" | wc -l) files"
log "worker stopped by request; remaining years to run: 1992 1993 1994 1995 1996"
