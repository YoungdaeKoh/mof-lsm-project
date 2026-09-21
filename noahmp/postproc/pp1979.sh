#!/bin/bash
source /home/ydkoh/anaconda3/etc/profile.d/conda.sh; conda activate
cd ~/HRLDAS/forcing_WFDE5_1deg/prod_1979_2023
for m in $(seq 1 12); do
  echo "=== 1979-$m $(date)"; python ldasout_6h_to_daymon.py 1979 $m --daily || { echo "FAILED month $m"; exit 1; }
done
echo "=== ALL DONE $(date)"
