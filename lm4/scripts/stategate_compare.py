#!/usr/bin/env python3
"""Compare two LM4p run dirs variable by variable: restarts and land/river history.

Bit-for-bit is the expectation for everything the land owns.  Atmosphere-side
restarts (fv_*, atmos_*, physics_driver, ...) are reported separately: with the
gate the frozen atmosphere is simply not touched, so they may legitimately differ.
usage: python stategate_compare.py <base_dir> <gate_dir>
"""
import glob
import os
import sys
import numpy as np
from netCDF4 import Dataset

a, b = sys.argv[1], sys.argv[2]
LAND = ("land", "soil", "vegn", "cana", "snow", "glac", "lake", "river", "fire", "landuse")


def cmpfile(fa, fb):
    """returns (n variables, n differing, worst variable, max abs diff)"""
    nd, worst, wmax = 0, "", 0.0
    with Dataset(fa) as A, Dataset(fb) as B:
        A.set_auto_mask(False); B.set_auto_mask(False)
        names = [v for v in A.variables if v in B.variables]
        missing = [v for v in A.variables if v not in B.variables]
        for v in names:
            x, y = A.variables[v][:], B.variables[v][:]
            if x.shape != y.shape:
                nd += 1; worst = v + "(shape)"; wmax = np.inf; continue
            if x.dtype.kind in "fiu":
                same = np.array_equal(x, y, equal_nan=True) if x.dtype.kind == "f" else np.array_equal(x, y)
                if not same:
                    d = float(np.nanmax(np.abs(x.astype("f8") - y.astype("f8"))))
                    nd += 1
                    if d >= wmax:
                        worst, wmax = v, d
            elif not np.array_equal(x, y):
                nd += 1; worst = worst or v
    return len(names), nd, worst, wmax, missing


def group(title, files):
    print("\n== %s (%d files)" % (title, len(files)))
    bad = 0
    for fa in files:
        fb = fa.replace(a, b, 1)
        if not os.path.exists(fb):
            print("  MISSING in gate: %s" % os.path.basename(fa)); bad += 1; continue
        n, nd, worst, wmax, missing = cmpfile(fa, fb)
        if nd or missing:
            bad += 1
            print("  DIFF %-40s %d/%d vars differ, worst %s max|d|=%.3e %s"
                  % (os.path.basename(fa), nd, n, worst, wmax, ("missing " + str(missing[:3])) if missing else ""))
    print("  -> %s" % ("ALL IDENTICAL" if bad == 0 else "%d file(s) differ" % bad))
    return bad


rs = sorted(glob.glob(a + "/RESTART/*.nc"))
land_rs = [f for f in rs if os.path.basename(f).split(".")[0].rstrip("12") in LAND]
other_rs = [f for f in rs if f not in land_rs]
hist = sorted(glob.glob(a + "/*.land_*.nc") + glob.glob(a + "/*.river_*.nc"))
nb = group("land restarts", land_rs)
nh = group("land / river history", hist)
group("other restarts (atmosphere, ice, coupler) - informational", other_rs)
for t in ("coupler.res", "landuse.res"):
    fa, fb = a + "/RESTART/" + t, b + "/RESTART/" + t
    if os.path.exists(fa) and os.path.exists(fb):
        print("%s identical: %s" % (t, open(fa).read() == open(fb).read()))
for f in sorted(glob.glob(a + "/*.land_month.tile1.nc")):
    g = f.replace(a, b, 1)
    na = Dataset(f).dimensions["time"].size
    ng = Dataset(g).dimensions["time"].size if os.path.exists(g) else -1
    print("monthly records %s: base %d, patched %d" % (os.path.basename(f), na, ng))
print("\nVERDICT: land state and land output %s" % ("BIT-FOR-BIT IDENTICAL" if nb + nh == 0 else "DIFFER"))
