#!/bin/bash
# Collect and compare finished offline speed-test variants (LM4 notes 13.71).
#   bash speedtest_collect.sh ctrl1m ddep1m [diag1m cons1m ...]
# 1. rsync clock_table.txt, config_diff.txt, pbs/esm4p5 log tails and the monthly history files of each
#    variant to /Volumes/data02/LM4P/cases/speedtest/<variant>/
# 2. timing table + speed-ups vs the first variant (phentest_timing.py)
# 3. bit comparison of every land/river history variable vs the first variant (phentest_bitcompare.py)
set -u
L=/Volumes/data02/LM4P/cases/speedtest; S=/Volumes/data01/MOF_LSM_project/lm4/scripts
R=/data2/ydkoh/lm4/RUN/phentest
mkdir -p $L
for v in "$@"; do
  mkdir -p $L/$v
  rsync -aq --include='*.nc' --include='clock_table.txt' --include='config_diff.txt' --include='field_table' --include='diag_table' \
        --exclude='*' climate:$R/$v/ $L/$v/
  ssh climate "grep -a -c FATAL $R/$v/esm4p5.log; grep -a -c -i nan $R/$v/esm4p5.log; tail -1 $R/$v/RESTART/coupler.res" \
      | tr '\n' ' ' | awk -v v=$v '{printf "%-8s FATAL %s (MOM parser notes expected: 4)  NaN-lines %s  end: %s %s %s\n", v, $1, $2, $3, $4, $5}'
done
echo; echo "=== timing (first variant = reference)"
/opt/homebrew/bin/python3 $S/phentest_timing.py $(for v in "$@"; do echo $L/$v/clock_table.txt; done)
ref=$1; shift
for v in "$@"; do
  echo; echo "=== bit comparison: $v vs $ref (history variables; 'VARIABLE not in reference' = new, missing-in-test = dropped diagnostics)"
  /opt/homebrew/bin/python3 $S/phentest_bitcompare.py $L/$ref $L/$v | tail -n 25
  echo "--- diagnostics present in $ref but dropped in $v:"
  /opt/homebrew/bin/python3 - $L/$ref $L/$v <<'EOF'
import glob, os, sys
from netCDF4 import Dataset
a, b = sys.argv[1:3]; n = 0
for fa in sorted(glob.glob(a + "/*.nc")):
    fb = os.path.join(b, os.path.basename(fa))
    if not os.path.exists(fb):
        print("  file dropped:", os.path.basename(fa)); n += 1; continue
    with Dataset(fa) as A, Dataset(fb) as B:
        miss = [v for v in A.variables if v not in B.variables]
        if miss: print("  %s: %d dropped (%s%s)" % (os.path.basename(fa), len(miss), " ".join(miss[:6]), " ..." if len(miss) > 6 else "")); n += len(miss)
print("  total dropped:", n)
EOF
done
