#!/bin/bash
# Start phasewfde5_d (CTRL + WFDE5 snow/rain phase, 2010) on climate00 (24 ranks) after dayllat_d has finished.
# Deployed on the server as RUN/queue_phasewfde5.sh; uses RUN/phentest_v4.sh (v3 is used by queue_dayllat.sh).
cd /data2/ydkoh/lm4/RUN
until grep -q "dayllat_d done" queue_dayllat.out 2>/dev/null; do sleep 300; done
echo "[$(date)] dayllat_d finished, starting phasewfde5_d"
bash phentest_v4.sh run phasewfde5_d
echo "[$(date)] phasewfde5_d done"
