#!/bin/bash
# Wait for the Noah-MP production job to finish, then submit the post-processing.
#   setsid nohup bash ~/HRLDAS/postproc_driver.sh > ~/nmp_postproc_driver.out 2>&1 < /dev/null &
# Success of the model run is judged by the final restart, not by the job's rc.
set -u
RUN=/home/ydkoh/HRLDAS/forcing_WFDE5_1deg/prod_1979_2023
FINAL=$RUN/RESTART.2024010103_DOMAIN1
log() { echo "[$(date +%F\ %T)] $*"; }
mkdir -p "$RUN/postproc"
while qstat -u ydkoh 2>/dev/null | grep -q nmp_prod; do sleep 600; done
if [ ! -f "$FINAL" ]; then
  log "model job left the queue without $FINAL -- not post-processing (resubmit run_prod.pbs to resume)"
  exit 1
fi
log "model complete: $FINAL present; $(ls $RUN | grep -c LDASOUT) LDASOUT files"
JID=$(qsub /home/ydkoh/HRLDAS/postproc_prod.pbs)
log "postproc job $JID"
while qstat "$JID" >/dev/null 2>&1; do sleep 120; done
log "postproc done; tail of postproc.log:"
tail -4 "$RUN/postproc.log"
