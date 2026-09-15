#!/bin/bash
# Pull the two LM4P runs down from climate00 to the data02 archive disk.
#
# Local directory names are the server case names verbatim, so that a path here
# and a path on climate00 name the same run and neither has to be translated:
#   lm4p_ctl_1979-2024   the production run, 1979-2023, WFDE5, 387 GB
#   lm4_spinup30         cycle 1, the WFDE5 continuation, 475 GB (in archive_c1/)
#
# Not to be confused with /Volumes/data02/LM4/spinup, which is the earlier
# 300-year GSWP3 static-vegetation spin-up (IC snapshots and notes, 11 GB).
#
# Production goes first: it is the run every analysis from here on uses, and if
# the transfer has to be cut short that is the half worth having.
#
# FORCING is skipped -- it holds symlinks into /data2/ydkoh/lm4/forcing_WFDE5_lm4p
# on the server, which would land here as dangling links.
#
# Restartable: rsync skips what already matches, so re-running after an
# interruption picks up where it stopped. --partial keeps half-sent files so a
# 79 MB history file does not start over.
set -u

SRC=climate:/data2/ydkoh/lm4/RUN
DST=/Volumes/data02/LM4P/cases
LOG=/Volumes/data02/LM4P/fetch.log

mkdir -p "$DST/lm4p_ctl_1979-2024" "$DST/lm4_spinup30" "$(dirname "$LOG")"

log(){ echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

# -a archive, -h human sizes, --partial keep interrupted files,
# --info=progress2 one running total rather than a line per file
RS="rsync -ah --partial --info=progress2 --exclude=FORCING/"

log "=== 1/2 production: lm4p_ctl_1979-2024 (387G) ==="
$RS "$SRC/lm4p_ctl_1979-2024/" "$DST/lm4p_ctl_1979-2024/" 2>&1 | tee -a "$LOG"
rc1=${PIPESTATUS[0]}
log "production rsync exit=$rc1  local size now $(du -sh "$DST/lm4p_ctl_1979-2024" 2>/dev/null | cut -f1)"

log "=== 2/2 cycle 1: lm4_spinup30 (475G) ==="
$RS "$SRC/lm4_spinup30/" "$DST/lm4_spinup30/" 2>&1 | tee -a "$LOG"
rc2=${PIPESTATUS[0]}
log "spinup rsync exit=$rc2  local size now $(du -sh "$DST/lm4_spinup30" 2>/dev/null | cut -f1)"

log "=== done. production=$rc1 spinup=$rc2 (0 = clean) ==="
