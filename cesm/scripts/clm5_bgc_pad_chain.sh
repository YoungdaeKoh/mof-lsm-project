#!/bin/bash
# Drive the CLM5-BGC post-AD spin-up in 10-year chunks.
#
# The AD phase ended at year 0211 with the soil carbon and nitrogen pools still
# on accelerated turnover.  This phase runs with spinup_state=0, which rescales
# them on the first read of finidat and then lets them settle at their real rate.
#
# Only the first chunk runs with CONTINUE_RUN=FALSE, so that finidat is read.
# After that the run continues from rpointer, and the driver passes FIRST=0.
#
# Guards mirror the AD chain: progress is judged by the restart year actually
# advancing, not by a file existing, and a hard counter caps the run.
# case.submit --no-batch exits 1 even on success, so its exit code is never used.
set -u

CASE=/home/ydkoh/CESM/cases/clm5_bgc_pad
RUN=/data2/ydkoh/cesm2_output/clm5_bgc_pad/run
PBS=$CASE/clm5_bgc_pad_chunk.pbs
LOG=$CASE/chain.log

TARGET_YEAR=${1:-100}      # post-AD length in years; convergence may come sooner
MAXCHUNK=15

log() { echo "[$(date +%F\ %T)] $*" | tee -a "$LOG"; }

year_now() {
  # rpointer.lnd looks like ./clm5_bgc_pad.clm2.r.0012-01-01-00000.nc
  sed -E 's/.*\.r\.([0-9]{4})-.*/\1/' "$RUN/rpointer.lnd" 2>/dev/null | head -1
}

# FIRST=1 means CONTINUE_RUN=FALSE, which makes CLM read finidat and start over
# at year 0001.  That is right on the very first launch and wrong on every
# resume: hard-coding it to 1 sent a restarted chain back to the AD restart and
# threw away the post-AD years already done.  The presence of rpointer is what
# distinguishes the two cases.
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
    y0=0001                       # RUN_STARTDATE; rpointer does not exist yet
    CHUNK_N=10
  else
    y0=$(year_now)
    case "$y0" in
      ''|*[!0-9]*) log "ABORT: cannot parse year from rpointer.lnd"; exit 1 ;;
    esac
    if [ "$((10#$y0))" -ge "$TARGET_YEAR" ]; then
      log "post-AD target reached: year $y0 >= $TARGET_YEAR"; break
    fi
    CHUNK_N=10
  fi

  log "chunk $chunk: submitting from year $y0, ${CHUNK_N} years (FIRST=$FIRST)"
  JID=$(qsub -v CHUNK_N="$CHUNK_N",FIRST="$FIRST" "$PBS")
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

log "post-AD complete at year $(year_now)."
