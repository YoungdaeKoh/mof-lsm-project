#!/usr/bin/env python
# CLM5-SP spin-up, both cycles, the six variables the official SpinupStability_SP.ncl watches:
#   FSH, EFLX_LH_TOT, FPSN(=photosynthesis, GPP proxy for SP), TWS, H2OSOI layer 8, TSOI layer 10.
# Annual (January monthly-mean) area-weighted global land mean. (SP output has no GPP field;
# FPSN "photosynthesis" is the leaf-level analog and is what SP writes.)
import glob, os, re
import numpy as np
from netCDF4 import Dataset

ARCH = [("1", "/home/ydkoh/CESM/spinup_raw/clm5_GSWP3_SP_cyc1"),
        ("2", "/home/ydkoh/CESM/spinup_raw/clm5_GSWP3_SP_cyc2")]
f0 = sorted(glob.glob(f"{ARCH[0][1]}/*.clm2.h0.*-01.nc"))[0]
d0 = Dataset(f0); d0.set_auto_mask(True)
area = d0.variables["area"][:].astype("f8"); lfr = d0.variables["landfrac"][:].astype("f8")
lmask = d0.variables["landmask"][:].astype("f8"); d0.close()
W = np.where((lmask > 0.5) & np.isfinite(area*lfr), area*lfr, 0.0)
def wm(a):
    a = np.ma.filled(a.astype("f8"), np.nan); m = np.isfinite(a) & (W > 0)
    return float(np.sum(a[m]*W[m]) / np.sum(W[m]))

print("cycle,spinyear,modelyear,FSH,LH,FPSN,TWS,H2OSOI_L8,TSOI_L10")
seq = 0
for cyc, A in ARCH:
    for f in sorted(glob.glob(f"{A}/*.clm2.h0.*-01.nc")):
        my = int(re.search(r"h0\.(\d{4})-01", os.path.basename(f)).group(1))
        if cyc == "2" and my == 2011:
            continue
        d = Dataset(f); d.set_auto_mask(True)
        row = (wm(d.variables["FSH"][0]), wm(d.variables["EFLX_LH_TOT"][0]),
               wm(d.variables["FPSN"][0]), wm(d.variables["TWS"][0]),
               wm(d.variables["H2OSOI"][0][7]), wm(d.variables["TSOI"][0][9]))
        d.close()
        seq += 1
        print("%s,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f" % ((cyc, seq, my) + row))
