#!/usr/bin/env python
# CLM5 SP spin-up, BOTH cycles (60 model-yr), guide-watched variables, area-weighted.
# Jan monthly-mean h0 snapshots. cyc1 = model 1981-2010, cyc2 = model 2011-2040 (same
# cyclic forcing 1981-2010). Convergence = same-forcing-phase drift: cyc1 yr30 vs cyc2 yr30.
# TSOI is read at layer 10 (1.36 m, the guide layer) AND the 42 m bottom node (to show the trap).
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

print("cycle,spinyear,modelyear,TSOI_L10,TSOI_bot,colwater,H2OSOI_L8,TWS,FSH,LH")
seq = 0
for cyc, A in ARCH:
    files = sorted(glob.glob(f"{A}/*.clm2.h0.*-01.nc"))
    for f in files:
        my = int(re.search(r"h0\.(\d{4})-01", os.path.basename(f)).group(1))
        # cyc2 first file (model 2011) == cyc1 end re-labeled; skip to avoid dup
        if cyc == "2" and my == 2011:
            continue
        d = Dataset(f); d.set_auto_mask(True)
        tsoi = d.variables["TSOI"][0]
        colw = d.variables["TOTSOILLIQ"][0] + d.variables["TOTSOILICE"][0]
        row = (wm(tsoi[9]), wm(tsoi[24]), wm(colw), wm(d.variables["H2OSOI"][0][7]),
               wm(d.variables["TWS"][0]), wm(d.variables["FSH"][0]), wm(d.variables["EFLX_LH_TOT"][0]))
        d.close()
        seq += 1
        print("%s,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f" % ((cyc, seq, my) + row))
