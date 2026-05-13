#!/bin/bash
# Run clm5_test02 on climate00 with multi-node (climate01:48, climate02:48) distribution

source /home/ydkoh/CESM2.module.sh

cd ~/CESM/cases/clm5_test02

echo "Starting clm5_test02 at $(date)"
echo "Cases directory: $(pwd)"
echo "DIN_LOC_ROOT: $(./xmlquery DIN_LOC_ROOT)"
echo "NTASKS: $(./xmlquery NTASKS)"
echo "STOP_N: $(./xmlquery STOP_N)"

./.case.run

echo "Completed at $(date)"
echo "Checking output..."
if [ -d run ]; then
    ls -lh run/*.clm2.h0.* 2>/dev/null | tail -5
fi
