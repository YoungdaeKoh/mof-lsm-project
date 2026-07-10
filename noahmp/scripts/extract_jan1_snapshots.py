#!/usr/bin/env python
# Verify the Jan-01 snapshots and measure the seasonal offset they remove.
#
# The spin-up's own restarts drift Jan-01 -> Dec-25 (fixed 8760 h stride vs a Gregorian
# calendar). LM4 runs noleap, so its restarts sit on Jan-01 every year. Each snapshot here
# was made by integrating the drifted restart forward to the next Jan-01 with identical
# forcing and physics, so it lies on the same continuous trajectory.
#
# Offset reported below = (state at Jan-01 of year Y+1) - (state at the drifted restart of
# year Y). That is the 1-7 days of model evolution that separated Noah-MP's snapshot from
# LM4's. It is not an error -- it is how far apart the two models' samples were.
#
# Emits CSV: year,deepT_noice,colw_noice,swe_noice,swe_ice  (all cos(lat)-weighted)
import glob
import os
import re

import numpy as np
from netCDF4 import Dataset

SETUP = "/home/ydkoh/HRLDAS/forcing_GSWP3_1deg/init/HRLDAS_setup_GSWP3_1deg_d01.nc"
SNAP = "/home/ydkoh/HRLDAS/forcing_GSWP3_1deg/jan1_snap/snapshots"
CYC2 = "/home/ydkoh/HRLDAS/spinup_raw/noahmp_GSWP3_1deg_staticveg_cyc2"
DZ = np.array([0.10, 0.30, 0.60, 1.00])
ICE, WATER = 15, 17

ds = Dataset(SETUP)
ds.set_auto_mask(False)
iv = ds.variables["IVGTYP"][0].astype(int)
xlat = ds.variables["XLAT"][0].astype("f8")
ds.close()
land = iv != WATER
noice = land & (iv != ICE)
ice = land & (iv == ICE)
wgt = np.cos(np.deg2rad(xlat))


def amean(a, m):
    return float(np.average(a[m], weights=wgt[m]))


def read(p):
    d = Dataset(p)
    d.set_auto_mask(False)
    times = b"".join(d.variables["Times"][0]).decode().strip()
    st = np.asarray(d["SOIL_T"][0], dtype="f8")
    sm = np.asarray(d["SMC"][0], dtype="f8")
    sn = np.asarray(d["SNEQV"][0], dtype="f8")
    nan = int(np.isnan(st).sum() + np.isnan(sm).sum() + np.isnan(sn).sum())
    d.close()
    return times, st[:, 3, :], 1000.0 * (sm * DZ[None, :, None]).sum(axis=1), sn, nan


files = sorted(glob.glob(f"{SNAP}/JAN1.*_DOMAIN1"))
bad = 0
rows = []
for f in files:
    yr = re.search(r"JAN1\.(\d{4})", os.path.basename(f)).group(1)
    times, deep, colw, sn, nan = read(f)
    if times != f"{yr}-01-01_00:00:00" or nan:
        bad += 1
        print(f"!! {os.path.basename(f)}: Times={times!r} NaN={nan}")
    rows.append((int(yr), amean(deep, noice), amean(colw, noice), amean(sn, noice), amean(sn, ice)))

print(f"# verified {len(files)} snapshots, {bad} bad", flush=True)
print("year,deepT_noice,colw_noice,swe_noice,swe_ice")
for r in rows:
    print("%d,%.6f,%.6f,%.6f,%.6f" % r)

# --- how large was the Dec-25 vs Jan-01 offset? -------------------------------------
DRIFT = {  # drifted restart of year Y -> snapshot at Jan-01 of year Y+1
    "1984123100": 1985, "1988123000": 1989, "1992122900": 1993, "1996122800": 1997,
    "2000122700": 2001, "2004122600": 2005, "2008122500": 2009, "2009122500": 2010,
}
print("\n# seasonal offset removed by the tails (drifted restart -> next Jan-01)", flush=True)
print("# rst_date        days  d(deepT) K   d(colw) kg/m2   d(swe) mm")
snap = {r[0]: r for r in rows}
for rst, yr in DRIFT.items():
    _, deep, colw, sn, _ = read(f"{CYC2}/RESTART.{rst}_DOMAIN1")
    d0 = (amean(deep, noice), amean(colw, noice), amean(sn, noice))
    _, d1T, d1W, d1S, _ = snap[yr]
    from datetime import date
    days = (date(yr, 1, 1) - date(int(rst[:4]), int(rst[4:6]), int(rst[6:8]))).days
    print("# %s  %4d   %+10.4f  %+12.4f  %+10.4f" % (rst, days, d1T - d0[0], d1W - d0[1], d1S - d0[2]))
