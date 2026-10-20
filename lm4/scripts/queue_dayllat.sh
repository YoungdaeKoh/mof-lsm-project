#!/bin/bash
# Start dayllat_d (autumn latitude-dependent threshold only) on climate00 (24 ranks) after daylhold5_d has finished.
# Deployed on the server as RUN/queue_dayllat.sh; uses RUN/phentest_v3.sh (phentest_v2.sh is still running daylhold5_d).
cd /data2/ydkoh/lm4/RUN
until grep -q "daylhold5_d done" queue_daylhold5.out 2>/dev/null; do sleep 300; done
echo "[$(date)] daylhold5_d finished, starting dayllat_d"
bash phentest_v3.sh run dayllat_d
echo "[$(date)] dayllat_d done"
