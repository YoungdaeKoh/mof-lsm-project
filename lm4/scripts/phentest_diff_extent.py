#!/usr/bin/env python3
"""How widespread are the differences between two phentest runs?  (follow-up to phentest_diff_onset.py)

Round-off from a rebuilt executable shows up as tiny differences in (almost) every cell from
the first step; a logic change shows up as large differences in a subset of cells.
Prints the share of land cells that differ and the size distribution of the differences for
the first 3-hourly record of mrsos and for the January-mean lai, t_ref, evap of land_month.
usage: python phentest_diff_extent.py <long_run_dir> <short_run_dir>
"""
import glob
import os
import sys
import numpy as np
from netCDF4 import Dataset

a, b = sys.argv[1], sys.argv[2]


def collect(stream, var, rec):
    xs, ys = [], []
    for fb in sorted(glob.glob(b + "/*.%s.tile*.nc" % stream)):
        with Dataset(os.path.join(a, os.path.basename(fb))) as A, Dataset(fb) as B:
            A.set_auto_mask(False); B.set_auto_mask(False)
            if var not in B.variables:
                return None, None
            y = B.variables[var][rec].astype("f8").ravel(); x = A.variables[var][rec].astype("f8").ravel()
            fill = getattr(B.variables[var], "_FillValue", None)
            ok = np.isfinite(x) & np.isfinite(y)
            if fill is not None:
                ok &= (x != fill) & (y != fill)
            xs.append(x[ok]); ys.append(y[ok])
    return np.concatenate(xs), np.concatenate(ys)


for stream, var, rec, label in (("land_8xdaily_inst", "mrsos", 0, "first 3-hourly record"),
                                ("land_8xdaily_inst", "mrsos", 7, "end of day 1"),
                                ("land_month", "lai", 0, "January mean"),
                                ("land_month", "t_ref", 0, "January mean"),
                                ("land_month", "evap", 0, "January mean"),
                                ("land_month", "gpp", 0, "January mean")):
    x, y = collect(stream, var, rec)
    if x is None:
        print("%-18s %-6s not in file" % (stream, var)); continue
    d = np.abs(x - y); rel = d / np.maximum(np.abs(x), 1e-30)
    nz = d > 0
    q = np.percentile(rel[nz], [50, 90, 99, 100]) if nz.any() else [0, 0, 0, 0]
    print("%-18s %-6s %-22s cells %6d differing %5.1f %% | rel diff of differing cells p50 %.1e p90 %.1e p99 %.1e max %.1e | mean ref %.6g test %.6g (%+.2e rel)"
          % (stream, var, label, x.size, 100.0 * nz.mean(), q[0], q[1], q[2], q[3], x.mean(), y.mean(), y.mean() / x.mean() - 1))
