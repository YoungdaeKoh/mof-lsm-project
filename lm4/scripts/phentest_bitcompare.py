#!/usr/bin/env python3
"""Bit-for-bit regression check between two phentest runs of different length.

The short run (e.g. noparam, 31 days) is compared with the leading records of the long
run (e.g. base, 365 days): every variable of every land/river history file, record by
record over the short run's time axis.  Restarts are not compared (different end dates).
Expectation for the phenoff exe without the new parameters: zero differing variables
(LM4 notes 13.69).
usage: python phentest_bitcompare.py <long_run_dir> <short_run_dir>
"""
import glob
import os
import sys
import numpy as np
from netCDF4 import Dataset

a, b = sys.argv[1], sys.argv[2]          # a = long reference run, b = short test run
files = sorted(glob.glob(b + "/*.land_*.nc") + glob.glob(b + "/*.river_*.nc"))
nfile = nvar = ndiff = nmiss = 0
worst = ("", "", 0.0)
streams = {}
for fb in files:
    fa = os.path.join(a, os.path.basename(fb))
    if not os.path.exists(fa):
        nmiss += 1
        print("MISSING in reference:", os.path.basename(fb))
        continue
    nfile += 1
    key = os.path.basename(fb).split(".")[1]
    s = streams.setdefault(key, [0, 0, 0])   # variables, differing, records
    with Dataset(fa) as A, Dataset(fb) as B:
        A.set_auto_mask(False); B.set_auto_mask(False)
        nt = len(B.dimensions["time"]) if "time" in B.dimensions else 0
        s[2] = nt
        for v in B.variables:
            if v not in A.variables:
                ndiff += 1; s[1] += 1
                print("VARIABLE not in reference:", os.path.basename(fb), v)
                continue
            vb, va = B.variables[v], A.variables[v]
            if "time" in vb.dimensions and vb.dimensions[0] == "time":
                y = vb[:]; x = va[:nt]
            else:
                y = vb[:]; x = va[:]
            nvar += 1; s[0] += 1
            if x.shape != y.shape:
                same = False; d = np.inf
            elif x.dtype.kind == "f":
                same = np.array_equal(x, y, equal_nan=True)
                d = 0.0 if same else float(np.nanmax(np.abs(x.astype("f8") - y.astype("f8"))))
            else:
                same = np.array_equal(x, y); d = 0.0 if same else 1.0
            if not same:
                ndiff += 1; s[1] += 1
                if d >= worst[2]:
                    worst = (os.path.basename(fb), v, d)
                if ndiff <= 10:
                    print("DIFF %s %s max|d|=%g" % (os.path.basename(fb), v, d))
print("stream: variables / differing / records compared")
for k in sorted(streams):
    print("  %-28s %5d / %3d / %4d" % (k, streams[k][0], streams[k][1], streams[k][2]))
print("files %d (missing %d)  variables %d  differing %d" % (nfile, nmiss, nvar, ndiff))
print("RESULT:", "BIT-IDENTICAL" if (ndiff == 0 and nmiss == 0 and nvar > 0) else
      "DIFFERENT  worst %s %s max|d|=%g" % worst)
