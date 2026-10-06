#!/usr/bin/env python3
"""Is the difference between two phentest runs one-sided (a rule acting) or symmetric (noise)?

If the new autumn rule were active without its parameters, leaves would be switched off where
days are shortening (the Southern Hemisphere in January) and LAI there would be systematically
LOWER in the test run.  Recompilation round-off gives increases and decreases in equal shares.
Prints, for January-mean lai of land_month, the share of cells with test > ref and test < ref,
the mean signed difference, by hemisphere, plus the largest decreases.
usage: python phentest_diff_sign.py <ref_run_dir> <test_run_dir>
"""
import glob
import os
import sys
import numpy as np
from netCDF4 import Dataset

a, b = sys.argv[1], sys.argv[2]
X, Y, LAT = [], [], []
for fb in sorted(glob.glob(b + "/*.land_month.tile*.nc")):
    with Dataset(os.path.join(a, os.path.basename(fb))) as A, Dataset(fb) as B:
        A.set_auto_mask(False); B.set_auto_mask(False)
        y = B.variables["lai"][0].astype("f8").ravel(); x = A.variables["lai"][0].astype("f8").ravel()
        latname = [v for v in ("geolat_t", "lat", "grid_yt") if v in B.variables][0]
        la = B.variables[latname][:].astype("f8").ravel()
        if la.size != y.size:
            la = np.repeat(la, y.size // la.size)
        fill = getattr(B.variables["lai"], "_FillValue", -1.0)
        ok = (x != fill) & (y != fill) & np.isfinite(x) & np.isfinite(y)
        X.append(x[ok]); Y.append(y[ok]); LAT.append(la[ok])
x = np.concatenate(X); y = np.concatenate(Y); lat = np.concatenate(LAT)
if np.abs(lat).max() < 4:      # radians
    lat = np.degrees(lat)
d = y - x
for name, m in (("all land", np.ones(d.size, bool)), ("NH (lat >= 0)", lat >= 0), ("SH (lat < 0)", lat < 0),
                ("SH 20-60S", (lat < -20) & (lat > -60))):
    dd, xx = d[m], x[m]
    print("%-14s cells %6d | test>ref %5.1f %%  test<ref %5.1f %%  equal %5.1f %% | mean LAI ref %.5f  mean diff %+.2e (%+.1e rel) | max increase %+.3f  max decrease %+.3f"
          % (name, dd.size, 100 * (dd > 0).mean(), 100 * (dd < 0).mean(), 100 * (dd == 0).mean(),
             xx.mean(), dd.mean(), dd.mean() / xx.mean(), dd.max(), dd.min()))
big = np.abs(d) > 0.05
print("cells with |diff| > 0.05 LAI: %d of %d ; of these decreases %d, increases %d" % (big.sum(), d.size, (d[big] < 0).sum(), (d[big] > 0).sum()))
