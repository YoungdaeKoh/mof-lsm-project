#!/bin/bash
# Run the two jobs of 2026-09-17 in order, unattended:
#   1. F2000climo f09 on 96 PEs (climate01 + climate02), one model year, for
#      the two-node timing -- F_2000climo_f09_96pe.pbs
#   2. then the CLM5-BGC production run 1979-2023 with WFDE5 forcing, driven
#      in 5-year chunks on climate01 -- clm5_prod_chain.sh
#
# Step 2 waits for step 1 because the F job holds both nodes.  Both steps are
# submitted through PBS from here; this script only waits, so it can sit on
# the login node under nohup:
#   nohup bash ~/run_scripts/run_F96_then_prod.sh >& ~/run_F96_then_prod.out &
#
# Guards, in the spirit of the chains: nothing is judged by an exit code, the
# production case must already be built, and the F step is skipped (not
# re-run) if its timing already exists.
set -u

RS=/home/ydkoh/run_scripts
FCASE=/home/ydkoh/CESM/cases/F_2000climo_f09_96pe
FPBS=$RS/F_2000climo_f09_96pe.pbs
PCASE=/home/ydkoh/CESM/cases/clm5_prod_1979_2023
PCHAIN=$PCASE/clm5_prod_chain.sh
END_YEAR=2023

log() { echo "[$(date +%F\ %T)] $*"; }

# ---------------------------------------------------------------- checks ----
[ -d "$FCASE" ] || { log "ABORT: F case missing: $FCASE"; exit 1; }
[ -d "$PCASE" ] || { log "ABORT: production case missing: $PCASE"; exit 1; }
[ -f "$PCHAIN" ] || { log "ABORT: chain script missing: $PCHAIN"; exit 1; }
built=$(cd "$PCASE" && ./xmlquery --value BUILD_COMPLETE)
[ "$built" = "TRUE" ] || { log "ABORT: production case not built (BUILD_COMPLETE=$built)"; exit 1; }

# The F case may still be building when this starts (F_f09_96pe_cam6clm5.csh
# takes ~30-40 min).  Wait for it rather than submitting a job that would fail
# at the BUILD_COMPLETE check; give up after a few hours so a broken build does
# not hold the production run hostage -- step 2 does not need the F case.
waited=0
until [ "$(cd "$FCASE" && ./xmlquery --value BUILD_COMPLETE 2>/dev/null)" = "TRUE" ]; do
  if [ "$waited" -ge 14400 ]; then
    log "step 1: F case still not built after 4 h -- skipping the F run"
    break
  fi
  [ "$waited" -eq 0 ] && log "step 1: waiting for the F case build (BUILD_COMPLETE)"
  sleep 300; waited=$((waited + 300))
done
fbuilt=$(cd "$FCASE" && ./xmlquery --value BUILD_COMPLETE 2>/dev/null)

# ---------------------------------------------------------------- step 1 ----
if [ "$fbuilt" != "TRUE" ]; then
  log "step 1: skipped (F case not built)"
elif ls "$FCASE"/timing/cesm_timing.F_2000climo_f09_96pe.* >/dev/null 2>&1; then
  log "step 1: timing already present, skipping the F 96-PE run"
else
  log "step 1: submitting F 96-PE (one model year, climate01+climate02)"
  JID=$(qsub "$FPBS")
  [ -n "$JID" ] || { log "ABORT: qsub returned nothing"; exit 1; }
  log "step 1: job $JID"
  while qstat "$JID" >/dev/null 2>&1; do sleep 300; done
  log "step 1: job $JID left the queue"
  echo "----- F 96-PE result -----"
  cat "$FCASE/run.log" 2>/dev/null | grep -E '^===|Model Cost|Model Throughput|Run Time|total pes' || true
  echo "--------------------------"
  if ! ls "$FCASE"/timing/cesm_timing.F_2000climo_f09_96pe.* >/dev/null 2>&1; then
    log "step 1: no timing file -- the F run did not finish; going on to step 2 anyway"
  fi
fi

# ---------------------------------------------------------------- step 2 ----
log "step 2: starting the production chain to $END_YEAR in $PCASE"
cd "$PCASE" || exit 1
bash "$PCHAIN" "$END_YEAR"
log "step 2: chain returned ($?)"
log "done."
