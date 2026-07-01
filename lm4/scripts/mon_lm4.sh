#!/bin/bash
RUNDIR=/data2/ydkoh/lm4/RUN/lm4_spinup
for i in $(seq 1 60); do
  sleep 300
  alive=$(ssh climate "qstat 2871" 2>/dev/null | grep -c "2871")
  lastfile=$(ssh climate "ls -t $RUNDIR/" 2>/dev/null | grep "cpl.hi.lnd" | head -1)
  nrst=$(ssh climate "ls $RUNDIR/RESTART/" 2>/dev/null | grep -oE '^[0-9]{8}' | sort -u | wc -l)
  echo "[iter $i $(date +%H:%M)] alive=$alive last=$lastfile yrly_restarts=$nrst"
  if [ "$alive" -eq 0 ]; then echo "JOB_ENDED"; break; fi
done
echo "=== MONITOR DONE $(date +%H:%M) ==="
ssh climate "tail -3 $RUNDIR/spinup.log" 2>/dev/null
ssh climate "ls -t $RUNDIR/" 2>/dev/null | grep "cpl.hi.lnd" | head -1
