#!/bin/bash
# Double-preserve Noah-MP spin-up restarts: climate server -> local Mac archive.
# Mirrors the LM4 preservation rule (lsm-spinup-raw-preservation):
#   - rsync WITHOUT --delete  ->  local copies are NEVER auto-removed.
#   - deletion is MANUAL by the user only.
# Server side accumulates via noahmp_spinup.pbs post-run rsync into spinup_raw/.
set -e
SRC=climate:/home/ydkoh/HRLDAS/spinup_raw/
DEST=/Volumes/data02/NOAHMP/spinup_raw
mkdir -p "$DEST"
echo "=== pulling Noah-MP spin-up archive: $(date) ==="
rsync -av "$SRC" "$DEST/"
n=$(find "$DEST" -name 'RESTART.*_DOMAIN1' 2>/dev/null | wc -l | tr -d ' ')
echo "=== done -> $DEST ($n restart files) ==="
