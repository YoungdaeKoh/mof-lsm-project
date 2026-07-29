#!/bin/bash
# Take over from chain_spinup30.sh after the running 1996 segment finishes.
#
# The old chain is killed first so it cannot submit 1997 with the old
# days=364/hours=21 (which would silently cost another December). Its PBS job
# keeps running regardless - the chain only polls qstat - so this script waits
# for that job, performs the same archive/hand-off the chain would have done,
# then starts chain_spinup30_v2.sh (days=365/hours=0) from 1997.
set -u
R=/data2/ydkoh/lm4/RUN/lm4_spinup30
JID=${1:-8305.climate00}
Y=1996
log() { echo "[$(date +%F\ %T)] handoff: $*" | tee -a "$R/chain.log"; }

log "waiting for $JID (y$Y) to finish"
while qstat "$JID" >/dev/null 2>&1; do sleep 120; done
log "$JID finished"

if grep -q 'FATAL' "$R/esm4p5.log" 2>/dev/null && \
   grep 'FATAL' "$R/esm4p5.log" | grep -qv FATAL_UNUSED_PARAMS; then
  log "ABORT: FATAL in y$Y"; exit 1
fi
n=$(ls "$R/RESTART"/*.res*.nc 2>/dev/null | wc -l)
if [ "$n" -lt 40 ]; then log "ABORT: y$Y wrote only $n restart files"; exit 1; fi

mkdir -p "$R/archive/y$Y"
cp -p "$R/RESTART"/*.res* "$R/archive/y$Y"/ 2>/dev/null
mv "$R"/*.land_*.nc "$R/archive/y$Y"/ 2>/dev/null
log "y$Y archived: $(ls "$R/archive/y$Y" | wc -l) files"

cp -p "$R/RESTART"/*.res* "$R/INPUT"/
log "restart handed to 1997; starting v2"

cd "$R"
nohup bash "$R/chain_spinup30_v2.sh" 1997 2010 >& "$R/chain_driver_v2.out" &
log "v2 started (pid $!)"
