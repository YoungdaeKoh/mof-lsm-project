#!/bin/bash
# Drive the CLM5 production run 1979-2023 in five-year chunks.
#
# BATCH_SYSTEM is none on this machine, so CESM's own RESUBMIT cannot chain and
# the chunks are submitted from outside.  Guards mirror the LM4 and post-AD
# chains: progress is judged by the restart year actually advancing, not by a
# file existing, and a hard counter caps the run.  case.submit --no-batch exits
# 1 even on success, so its exit code is never used as a test.
#
# Only the first chunk runs with CONTINUE_RUN=FALSE, so that finidat -- the
# post-AD final restart -- is read.  After that the run continues from rpointer.
set -u

CASE=/home/ydkoh/CESM/cases/clm5_prod_1979_2023
RUN=/data2/ydkoh/cesm2_output/clm5_prod_1979_2023/run
PBS=$CASE/clm5_prod_chunk.pbs
LOG=$CASE/chain.log

END_YEAR=${1:-2023}
CHUNK=5
MAXCHUNK=15

log() { echo "[$(date +%F\ %T)] $*" | tee -a "$LOG"; }

year_now() {
  # rpointer.lnd looks like ./clm5_prod_1979_2023.clm2.r.1984-01-01-00000.nc
  sed -E 's/.*\.r\.([0-9]{4})-.*/\1/' "$RUN/rpointer.lnd" 2>/dev/null | head -1
}

# FIRST=1 means CONTINUE_RUN=FALSE, which makes CLM read finidat and start over.
# That is right on the first launch and wrong on every resume, so it is decided
# by whether rpointer exists rather than hard-coded.
chunk=0
if [ -f "$RUN/rpointer.lnd" ]; then
  FIRST=0
  echo "resuming from $(cat "$RUN/rpointer.lnd")"
else
  FIRST=1
  echo "no rpointer: starting from finidat"
fi
while :; do
  chunk=$((chunk + 1))
  [ "$chunk" -le "$MAXCHUNK" ] || { log "ABORT: chunk cap $MAXCHUNK reached"; exit 1; }

  if [ "$FIRST" = "1" ]; then
    y0=1979                       # RUN_STARTDATE; rpointer does not exist yet
  else
    y0=$(year_now)
    case "$y0" in
      ''|*[!0-9]*) log "ABORT: cannot parse year from rpointer.lnd"; exit 1 ;;
    esac
    if [ "$((10#$y0))" -gt "$END_YEAR" ]; then
      log "production complete: reached year $y0"; break
    fi
  fi

  # do not overshoot the end year
  n=$CHUNK
  if [ "$((10#$y0 + n - 1))" -gt "$END_YEAR" ]; then
    n=$((END_YEAR - 10#$y0 + 1))
  fi
  [ "$n" -ge 1 ] || { log "production complete at year $y0"; break; }

  log "chunk $chunk: from $y0, $n years (FIRST=$FIRST)"
  JID=$(qsub -v CHUNK_N="$n",FIRST="$FIRST" "$PBS")
  [ -n "$JID" ] || { log "ABORT: qsub returned nothing"; exit 1; }
  log "chunk $chunk: job $JID"
  while qstat "$JID" >/dev/null 2>&1; do sleep 300; done

  y1=$(year_now)
  case "$y1" in
    ''|*[!0-9]*) log "ABORT: rpointer unreadable after chunk $chunk"; exit 1 ;;
  esac
  if [ "$FIRST" = "0" ] && [ "$((10#$y1))" -le "$((10#$y0))" ]; then
    log "ABORT: year did not advance ($y0 -> $y1); stale restart, would loop"
    exit 1
  fi
  log "chunk $chunk done: $y0 -> $y1"
  FIRST=0
done

log "chain finished at year $(year_now)."
