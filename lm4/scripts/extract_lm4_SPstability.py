#!/usr/bin/env python
# LM4 spin-up STATE-equilibrium check (last 30-yr segment of the 300-yr spin-up = cycle 10,
# already at equilibrium). Annual Jan-01 soil.res restarts, 6 tiles concatenated, unweighted
# land mean (cubed sphere ~ equal area, per lm4_equil.py). Same purpose as Noah-MP: confirm
# equilibrium at depth, per model -- similar depths, not a cross-model comparison.
# Layers (zfull node depth): soil water index 8 (0.70 m), soil temp index 10 (1.20 m).
import glob, os, re
import numpy as np
from netCDF4 import Dataset

RST = "/data2/ydkoh/lm4/RUN/lm4_spinup/RESTART"
IWATER, ITEMP = 8, 10   # 0.70 m, 1.20 m

def landmean_layer(files, var, layer=None):
    vals = []
    for t in range(1, 7):
        p = f"{files}/{{d}}.soil.res.tile{t}.nc"
    return None

years = sorted({m.group(1) for f in os.listdir(RST)
                if "soil.res.tile1" in f for m in [re.match(r"(\d{4})", f)] if m})

def lm(arr):
    a = np.ma.masked_greater(np.ma.masked_invalid(arr.astype("f8")), 1e10)
    return float(a.mean())

print("year,SW_070,ST_120,colwater,groundwater")
for y in years:
    sw, st, cw, gw = [], [], [], []
    for t in range(1, 7):
        fp = f"{RST}/{y}0101.000000.soil.res.tile{t}.nc"
        if not os.path.exists(fp):
            continue
        d = Dataset(fp); d.set_auto_mask(False)
        wl = d.variables["wl"][:].astype("f8"); ws = d.variables["ws"][:].astype("f8")
        temp = d.variables["temp"][:].astype("f8"); gwv = d.variables["groundwater"][:].astype("f8")
        d.close()
        w = wl + ws
        for arr in (wl, ws, temp, gwv):
            arr[np.abs(arr) > 1e10] = np.nan
        sw.append((wl[IWATER] + ws[IWATER]))
        st.append(temp[ITEMP])
        cw.append(np.nansum(np.where(np.abs(w) < 1e10, w, np.nan), axis=0))
        gw.append(np.nansum(np.where(np.abs(gwv) < 1e10, gwv, np.nan), axis=0))
    sw = np.concatenate(sw); st = np.concatenate(st); cw = np.concatenate(cw); gw = np.concatenate(gw)
    def m(a): 
        a = a[np.isfinite(a)]; return float(a.mean())
    print("%s,%.4f,%.4f,%.4f,%.4f" % (y, m(sw), m(st), m(cw), m(gw)))
