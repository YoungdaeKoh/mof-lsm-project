#!/usr/bin/env python3
"""Cycle-to-cycle convergence of the FAST carbon pools, CLM5 and LM4p, native grids.

CLM5  post-AD years 171 vs 201 (both forcing year 2001: post-AD year 1 = 1981,
      30-yr cycling) - annual mean of 12 monthly h0, f09, non-ice (PCT_GLACIER < 50),
      weights area*landfrac.  Pools LEAFC, FROOTC, LITR1C (metabolic litter), SOIL1C (fast SOM).
LM4p  spin-up cycle 1 y2010 vs ctl y2010 (ctl = cycle 2), Jan-Nov mean of land_month_cmip,
      C96, non-ice (soil points minus Greenland, as extract_monthly_noice.py), unweighted
      (quasi-equal-area).  Pools cLeaf, cRoot, cLitter (no fast/slow soil split is written).
Per cell: |X_B - X_A| / X_A, cells with X_A below a small floor are skipped (noise).
"""
import sys
import numpy as np
from netCDF4 import Dataset

sys.path.insert(0, "/data2/ydkoh/lm4")
from greenland_mask import in_greenland


def report(model, name, a, b, w, floor):
    ok = np.isfinite(a) & np.isfinite(b) & (w > 0) & (a > floor)
    rel = np.abs(b - a)[ok] / a[ok]
    ma = (a[ok] * w[ok]).sum() / w[ok].sum(); mb = (b[ok] * w[ok]).sum() / w[ok].sum()
    print("%-5s %-8s cells %6d | mean %10.4g -> %10.4g (%+7.3f %%) | cells <=1%% %5.1f %%  <=5%% %5.1f %%  median %.2f %%"
          % (model, name, ok.sum(), ma, mb, 100 * (mb - ma) / ma, 100 * np.mean(rel <= 0.01),
             100 * np.mean(rel <= 0.05), 100 * np.median(rel)))


# ---------------- CLM5 ----------------
P = "/home/ydkoh/CESM/spinup_raw/clm5_BGC_PAD/clm5_bgc_pad.clm2.h0.%04d-%02d.nc"
SURF = ("/data1/CESM2_INPUT/lnd/clm2/surfdata_map/release-clm5.0.18/"
        "surfdata_0.9x1.25_hist_16pfts_Irrig_CMIP6_simyr2000_c190214.nc")
with Dataset(P % (201, 1)) as d:
    d.set_auto_mask(False)
    area = d.variables["area"][:].astype("f8"); lfr = d.variables["landfrac"][:].astype("f8")
    lmask = d.variables["landmask"][:]
with Dataset(SURF) as s:
    s.set_auto_mask(False)
    glac = s.variables["PCT_GLACIER"][:].astype("f8")
W = np.where((lmask > 0.5) & (glac < 50) & np.isfinite(area * lfr), area * lfr, 0.0)
POOLS = ["LEAFC", "FROOTC", "LITR1C", "SOIL1C"]


def clm_year(y):
    acc = {v: 0.0 for v in POOLS}
    for m in range(1, 13):
        with Dataset(P % (y, m)) as d:
            d.set_auto_mask(False)
            for v in POOLS:
                x = d.variables[v][0].astype("f8"); x[np.abs(x) > 1e30] = np.nan
                acc[v] = acc[v] + x / 12.0
    return acc


A, B = clm_year(171), clm_year(201)
print("CLM5 post-AD year 171 vs 201 (forcing year 2001), gC/m2")
for v in POOLS:
    report("CLM5", v, A[v], B[v], W, 1.0)

# ---------------- LM4p ----------------
C1 = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive_c1/y2010/20100101.land_month%s.tile%d.nc"
C2 = "/data2/ydkoh/lm4/RUN/lm4p_ctl_1979-2024/archive/y2010/20100101.land_month%s.tile%d.nc"
LP = ["cLeaf", "cRoot", "cLitter"]
va = {v: [] for v in LP}; vb = {v: [] for v in LP}; wl = []
for t in range(1, 7):
    with Dataset(C1 % ("", t)) as d:
        lai = np.ma.filled(d.variables["lai"][0].astype("f8"), np.nan)
        lat = np.array(d.variables["geolat_t"][:]); lon = np.array(d.variables["geolon_t"][:])
    soil = np.isfinite(lai) & (np.abs(lai) < 1e30)
    wl.append((soil & ~in_greenland(lat, lon)).astype("f8").ravel())
    for src, store in ((C1, va), (C2, vb)):
        with Dataset(src % ("_cmip", t)) as d:
            for v in LP:
                x = np.ma.filled(d.variables[v][:11].astype("f8"), np.nan)    # Jan-Nov
                x[np.abs(x) > 1e30] = np.nan
                store[v].append(np.nanmean(x, axis=0).ravel())
wl = np.concatenate(wl)
print("\nLM4p spin-up cycle 1 y2010 vs ctl y2010 (cycle 2), Jan-Nov, kgC/m2")
for v in LP:
    report("LM4p", v, np.concatenate(va[v]), np.concatenate(vb[v]), wl, 1e-3)
