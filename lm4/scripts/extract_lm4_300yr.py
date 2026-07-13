#!/usr/bin/env python
# LM4 FULL 300-yr spin-up trajectory from the archived IC milestones (soil.res at each
# 30-yr segment end, Jan-01 -- same phase, comparable). Cold-start -> 300-yr equilibrium.
# soil water 0.70 m, soil temp 1.20 m, column water. 6 tiles, unweighted land mean.
import os
import numpy as np
from netCDF4 import Dataset

BASE = "/data2/ydkoh/lm4"
MILE = [("IC_GSWP3_staticveg_spin30", 30), ("IC_static_60yr", 60), ("IC_static_90yr", 90),
        ("IC_static_120yr", 120), ("IC_static_150yr", 150), ("IC_static_180yr", 180),
        ("IC_static_210yr", 210), ("IC_static_240yr", 240), ("IC_static_270yr", 270),
        ("IC_static_300yr", 300)]
IWATER, ITEMP = 8, 10

def lm(a):
    a = a[np.isfinite(a) & (np.abs(a) < 1e10)]; return float(a.mean())

print("year,SW_070,ST_120,colwater")
for sub, yr in MILE:
    d0 = f"{BASE}/{sub}"
    sw, st, cw = [], [], []
    ok = True
    for t in range(1, 7):
        fp = f"{d0}/20100101.000000.soil.res.tile{t}.nc"
        if not os.path.exists(fp):
            ok = False; break
        d = Dataset(fp); d.set_auto_mask(False)
        wl = d.variables["wl"][:].astype("f8"); ws = d.variables["ws"][:].astype("f8")
        temp = d.variables["temp"][:].astype("f8"); d.close()
        w = wl + ws
        sw.append(w[IWATER]); st.append(temp[ITEMP])
        cw.append(np.nansum(np.where(np.abs(w) < 1e10, w, np.nan), axis=0))
    if not ok:
        continue
    sw = np.concatenate(sw); st = np.concatenate(st); cw = np.concatenate(cw)
    print("%d,%.5f,%.4f,%.3f" % (yr, lm(sw), lm(st), lm(cw)))
