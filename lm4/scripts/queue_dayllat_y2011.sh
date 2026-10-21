#!/bin/bash
# Start dayllat_y2011_d (year 2 of the DLLAT chain: 2011 from dayllat_d/RESTART) on climate00 (24 ranks)
# after phasewfde5_d has finished. Restart-chain test before the 15-yr FULL run (decisions 2026-10-21).
# Deployed on the server as RUN/queue_dayllat_y2011.sh; uses RUN/phentest_v5.sh (v4 is used by queue_phasewfde5.sh).
cd /data2/ydkoh/lm4/RUN
until grep -q "phasewfde5_d done" queue_phasewfde5.out 2>/dev/null; do sleep 300; done
echo "[$(date)] phasewfde5_d finished, starting dayllat_y2011_d"
bash phentest_v5.sh run dayllat_y2011_d
echo "[$(date)] dayllat_y2011_d done"
