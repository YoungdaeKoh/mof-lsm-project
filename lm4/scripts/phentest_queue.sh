#!/bin/bash
# Run staged phentest variants one after another on climate00 (24 ranks each, outside PBS), after a
# running variant has finished. climate01/02 are busy (production run / other users), so only one
# 24-rank test at a time on the NFS server node (climate00-nfs-server-load).
#   nohup bash phentest_queue.sh larixlma_d daylspring5_d spring5_d >& phentest_queue.out &
# $1 = variant already running (wait for its model.x to exit), $2.. = variants to run in order.
cd /data2/ydkoh/lm4/RUN || exit 1
W=$1; shift
while pgrep -f "phentest/$W/model.x|phentest.sh run $W" > /dev/null; do sleep 300; done
echo "[$(date '+%F %T')] $W finished: $(tail -1 phentest/$W/RESTART/coupler.res 2>/dev/null)"
for v in "$@"; do
  if [ -s phentest/$v/RESTART/coupler.res ]; then echo "[$(date '+%F %T')] $v already finished, skip"; continue; fi
  echo "[$(date '+%F %T')] $v start"
  bash phentest.sh run $v > phentest_$v.out 2>&1
  echo "[$(date '+%F %T')] $v end: $(tail -1 phentest/$v/RESTART/coupler.res 2>/dev/null)"
done
