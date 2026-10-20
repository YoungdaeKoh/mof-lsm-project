#!/usr/bin/env python3
"""Does the 5-day smoothed spring gate (daylspring5) switch leaves on in winter warm spells? 2010, daily LAI, C96.

Runs: dayl_d (DL13/12, 20-day gate) and daylspring5_full_d (same autumn + 5-day gate), same seed (ctl y2009).
Per C96 cell (dayl_d LAI range > 0.3), over doy 1-120:
  winter rise  = LAI(doy 59, end of Feb) - LAI(doy 1) > 0.1
  false start  = LAI rose >= 0.1 above its doy-1 value and later fell back by >= half of that rise before doy 120
  leaf-on      = first day with LAI > LAI(doy 1) + 10 % of the doy 1..365 range (as spring_gate_diag.py, from doy 1)
Groups: latitude bands and AR6 ENA / EAS / WCE. Plain means/medians (C96 quasi equal area).
output: ../data/winter_false_start_2010.txt
"""
import glob
import shapely
import numpy as np
import regionmask
from netCDF4 import Dataset

R = "/Volumes/data02/LM4P/cases/phentest_2010/"
RUNS = [("DL", "dayl_d"), ("DLS5", "daylspring5_full_d"), ("DLH5", "daylhold5_d")]   # DLH5 = DLS5 + spring 12 h floor
RUNS = [r for r in RUNS if glob.glob(R + r[1] + "/20100101.land_daily.tile1.nc")]


def load(run):
    lai, lat, lon = [], [], []
    for f in sorted(glob.glob(R + run + "/20100101.land_daily.tile*.nc")):
        with Dataset(f) as A:
            A.set_auto_mask(False)
            lai.append(A["lai"][:].astype("f8").reshape(365, -1))
            lat.append(A["geolat_t"][:].ravel()); lon.append(A["geolon_t"][:].ravel())
    lai = np.concatenate(lai, 1); lai[(lai < 0) | (lai > 1e10)] = np.nan
    lon = np.concatenate(lon); return lai, np.concatenate(lat), np.where(lon > 180, lon - 360, lon)


L = {}
for k, run in RUNS:
    L[k], lat, lon = load(run)
ok = np.isfinite(L["DL"]).all(0) & np.isfinite(L["DLS5"]).all(0) & (np.nanmax(L["DL"], 0) - np.nanmin(L["DL"], 0) > 0.3)


def metrics(x):
    x0 = x[0]
    winter = (x[58] - x0) > 0.1
    rmax = np.maximum.accumulate(x[:120], 0)
    rise = rmax - x0; drop = rmax - x[:120]
    false = ((rise >= 0.1) & (drop >= 0.5 * rise)).any(0)
    thr = x0 + 0.1 * (x.max(0) - x.min(0))
    above = x > thr
    on = np.where(above.any(0), above.argmax(0) + 1, np.nan)
    return winter, false, on


M = {k: metrics(L[k]) for k in L}
ar6 = regionmask.defined_regions.ar6.land
GROUPS = [("20-30N", (lat >= 20) & (lat < 30)), ("30-40N", (lat >= 30) & (lat < 40)), ("40-50N", (lat >= 40) & (lat < 50)),
          ("50-70N", (lat >= 50) & (lat < 70))] + \
         [(c, shapely.contains_xy(ar6[c].polygon, lon, lat)) for c in ("ENA", "EAS", "WCE")]
out = ["Winter / early-spring behaviour, 2010 daily LAI, C96 cells with DL LAI range > 0.3",
       "%-7s %5s | %-13s | %-13s | %-17s | %-15s" % ("group", "cells", "winter rise %", "false start %", "leaf-on med doy", "Feb LAI mean")]
for name, sel in GROUPS:
    m = ok & sel
    w = [100 * M[k][0][m].mean() for k in L]; fs = [100 * M[k][1][m].mean() for k in L]
    on = [np.nanmedian(M[k][2][m]) for k in L]; feb = [L[k][31:59, m].mean() for k in L]
    j = lambda a, f: " -> ".join(f % x for x in a)
    out.append("%-7s %5d | %s | %s | %s | %s" % (name, m.sum(), j(w, "%5.1f"), j(fs, "%5.1f"), j(on, "%5.0f"), j(feb, "%5.2f")))
open("../data/winter_false_start_2010.txt", "w").write("\n".join(out) + "\n"); print("\n".join(out))
