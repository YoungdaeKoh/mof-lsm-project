#!/usr/bin/env python3
"""When and how large do two phentest runs start to differ?  (follow-up to phentest_bitcompare.py)

Prints, for the 3-hourly instantaneous stream and the daily stream, the first record at which
each differing variable departs from the reference and how the max |difference| grows.
A round-off origin shows as a tiny first difference that grows; a logic change shows as a
large difference from its first record.
usage: python phentest_diff_onset.py <long_run_dir> <short_run_dir>
"""
import glob
import os
import sys
import numpy as np
from netCDF4 import Dataset

a, b = sys.argv[1], sys.argv[2]
for stream, picks in (("land_8xdaily_inst", (0, 1, 2, 7, 15, 39, 79, 159, 247)),
                      ("land_daily", (0, 1, 2, 4, 9, 19, 30))):
    print("==", stream, "(record index: max|d| / max|ref|) summed over the six tiles' maxima")
    acc = {}
    for fb in sorted(glob.glob(b + "/*.%s.tile*.nc" % stream)):
        fa = os.path.join(a, os.path.basename(fb))
        with Dataset(fa) as A, Dataset(fb) as B:
            A.set_auto_mask(False); B.set_auto_mask(False)
            nt = len(B.dimensions["time"])
            for v in B.variables:
                vb = B.variables[v]
                if vb.dimensions[:1] != ("time",) or vb.dtype.kind != "f" or v.startswith(("average_", "time")):
                    continue
                y = vb[:].astype("f8"); x = A.variables[v][:nt].astype("f8")
                fill = getattr(vb, "_FillValue", None)
                if fill is not None:
                    m = (y == fill) | (x == fill); x = np.where(m, 0, x); y = np.where(m, 0, y)
                ax = tuple(range(1, y.ndim))
                d = np.abs(x - y).max(axis=ax); r = np.abs(x).max(axis=ax)
                e = acc.setdefault(v, [np.zeros(nt), np.zeros(nt)])
                e[0] = np.maximum(e[0], d); e[1] = np.maximum(e[1], r)
    same = [v for v, e in acc.items() if e[0].max() == 0]
    print("   identical in all records:", len(same), "of", len(acc), "->", " ".join(sorted(same))[:300])
    for v, e in sorted(acc.items()):
        if e[0].max() == 0:
            continue
        first = int(np.argmax(e[0] > 0))
        print("   %-18s first diff at record %3d | " % (v, first) +
              "  ".join("%d: %.1e/%.1e" % (i, e[0][i], e[1][i]) for i in picks if i < e[0].size))
