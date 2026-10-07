#!/usr/bin/env python3
"""Daily regional-mean LAI from land_daily on the native C96 tiles, to look for autumn re-leafing.

Prints the daily mean LAI over a latitude band for a date window, the day-to-day changes, and
flags days when the band mean rises again after the autumn decline has started.
usage: python phentest_daily_lai_band.py <run_dir> [lat0 lat1] [doy0 doy1]
"""
import glob
import os
import sys
import numpy as np
from netCDF4 import Dataset

run = sys.argv[1]
lat0, lat1 = (float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else (50.0, 70.0)
d0, d1 = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (213, 334)   # Aug 1 .. Nov 30
num = None; den = 0.0
for f in sorted(glob.glob(run + "/*.land_daily.tile*.nc")):
    with Dataset(f) as A:
        A.set_auto_mask(False)
        if "lai" not in A.variables:
            sys.exit("no daily lai in " + f)
        lat = A.variables["geolat_t"][:].astype("f8").ravel()
        w = np.ones(lat.size)
        fs = f.replace("land_daily", "land_static")
        if os.path.exists(fs):
            with Dataset(fs) as S:
                S.set_auto_mask(False)
                for n in ("land_area", "area_land", "soil_area"):
                    if n in S.variables:
                        w = np.squeeze(S.variables[n][:]).astype("f8").ravel(); w = np.where(w > 0, w, 0.0); break
        m = (lat >= lat0) & (lat < lat1)
        x = A.variables["lai"][:].astype("f8").reshape(A.variables["lai"].shape[0], -1)
        x = np.where((x == getattr(A.variables["lai"], "_FillValue", -1.0)) | ~np.isfinite(x), 0.0, x)
        s = (x[:, m] * w[m]).sum(1)
        num = s if num is None else num + s; den += w[m].sum()
lai = num / den
doy = np.arange(1, lai.size + 1)
sel = (doy >= d0) & (doy <= d1)
print("band %g-%gN, run %s, daily band-mean LAI (land_area weights)" % (lat0, lat1, os.path.basename(run)))
print("doy: " + " ".join("%3d" % k for k in doy[sel][::5]))
print("lai: " + " ".join("%3.1f" % v for v in lai[sel][::5]))
dl = np.diff(lai)
peak = int(np.argmax(lai)) + 1
rise = [(int(k) + 2, float(dl[k])) for k in range(lai.size - 1) if k + 2 > peak and dl[k] > 0.005]
print("peak day %d (LAI %.2f); after the peak, days with a rise > 0.005/day: %d" % (peak, lai.max(), len(rise)))
for k, v in rise[:12]:
    print("   doy %3d  +%.3f" % (k, v))
print("LAI at doy 244 (Sep 1) %.2f, 258 (Sep 15) %.2f, 274 (Oct 1) %.2f, 288 (Oct 15) %.2f, 305 (Nov 1) %.2f" % tuple(lai[k - 1] for k in (244, 258, 274, 288, 305)))
