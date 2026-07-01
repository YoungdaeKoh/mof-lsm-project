#!/usr/bin/env python3
# Full spin-up equilibrium diagnostic: all physical reservoirs, annual land-mean
# (unweighted over land points, 6 tiles), from yearly soil.res + snow.res restarts.
import os, re
import numpy as np
from netCDF4 import Dataset

RST = "/data2/ydkoh/lm4/RUN/lm4_spinup/RESTART"
years = sorted({m.group(1) for f in os.listdir(RST) if "soil.res.tile1" in f
                for m in [re.match(r"(\d{4})", f)] if m})

def lm(arr):  # land-mean over valid points
    a = np.array(arr, dtype=float)
    a = a[a < 1e30]
    return float(a.mean()) if a.size else np.nan

print(f"{'yr':>5} {'soilT_top':>10} {'soilT_deep':>11} {'soilWat':>9} {'grdwat':>9} {'snowWat':>9}")
prev = None
for y in years:
    Ttop, Tdeep, sw, gw, snw = [], [], [], [], []
    for t in range(1, 7):
        s = Dataset(f"{RST}/{y}0101.000000.soil.res.tile{t}.nc")
        temp = np.array(s.variables["temp"][:], float)      # (zfull, gp)
        wl = np.array(s.variables["wl"][:], float)
        ws = np.array(s.variables["ws"][:], float)
        grd = np.array(s.variables["groundwater"][:], float)
        s.close()
        Ttop.append(temp[0]); Tdeep.append(temp[-1])
        sw.append(np.where(wl < 1e30, wl, 0).sum(0) + np.where(ws < 1e30, ws, 0).sum(0))
        gw.append(np.where(grd < 1e30, grd, 0).sum(0))
        n = Dataset(f"{RST}/{y}0101.000000.snow.res.tile{t}.nc")
        nwl = np.array(n.variables["wl"][:], float); nws = np.array(n.variables["ws"][:], float)
        n.close()
        snw.append(np.where(nwl < 1e30, nwl, 0).sum(0) + np.where(nws < 1e30, nws, 0).sum(0))
    vals = [lm(np.concatenate(Ttop)), lm(np.concatenate(Tdeep)),
            lm(np.concatenate(sw)), lm(np.concatenate(gw)), lm(np.concatenate(snw))]
    d = "" if prev is None else "  d=" + " ".join(f"{vals[k]-prev[k]:+.3f}" for k in range(5))
    print(f"{y:>5} {vals[0]:>10.4f} {vals[1]:>11.4f} {vals[2]:>9.2f} {vals[3]:>9.2f} {vals[4]:>9.2f}{d}")
    prev = vals
