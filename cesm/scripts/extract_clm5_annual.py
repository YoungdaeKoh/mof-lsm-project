#!/usr/bin/env python
# CLM5-SP spin-up stability, ANNUAL MEAN (average the 12 monthly h0 per model-year),
# both cycles. Removes the January/seasonal bias -- proper day+night, all-season means,
# the conventional spin-up metric. Six SpinupStability_SP variables, area-weighted.
import glob, os, re
import numpy as np
from netCDF4 import Dataset

ARCH = [("1", "/home/ydkoh/CESM/spinup_raw/clm5_GSWP3_SP_cyc1"),
        ("2", "/home/ydkoh/CESM/spinup_raw/clm5_GSWP3_SP_cyc2")]
f0 = sorted(glob.glob(f"{ARCH[0][1]}/*.clm2.h0.*.nc"))[0]
d0 = Dataset(f0); d0.set_auto_mask(True)
area = d0.variables["area"][:].astype("f8"); lfr = d0.variables["landfrac"][:].astype("f8")
lmask = d0.variables["landmask"][:].astype("f8"); d0.close()
W = np.where((lmask > 0.5) & np.isfinite(area*lfr), area*lfr, 0.0)
def wm(a):
    a = np.ma.filled(a.astype("f8"), np.nan); m = np.isfinite(a) & (W > 0)
    return float(np.sum(a[m]*W[m]) / np.sum(W[m]))

def year_mean(files):
    """area-weighted global mean of each var, then average the 12 monthly means."""
    acc = {k: [] for k in ["FSH", "LH", "FPSN", "TWS", "H2OSOI_L8", "TSOI_L10"]}
    for f in files:
        d = Dataset(f); d.set_auto_mask(True)
        acc["FSH"].append(wm(d.variables["FSH"][0]))
        acc["LH"].append(wm(d.variables["EFLX_LH_TOT"][0]))
        acc["FPSN"].append(wm(d.variables["FPSN"][0]))
        acc["TWS"].append(wm(d.variables["TWS"][0]))
        acc["H2OSOI_L8"].append(wm(d.variables["H2OSOI"][0][7]))
        acc["TSOI_L10"].append(wm(d.variables["TSOI"][0][9]))
        d.close()
    return {k: np.mean(v) for k, v in acc.items()}

print("cycle,spinyear,modelyear,FSH,LH,FPSN,TWS,H2OSOI_L8,TSOI_L10")
seq = 0
for cyc, A in ARCH:
    years = sorted({re.search(r"h0\.(\d{4})-\d{2}", os.path.basename(f)).group(1)
                    for f in glob.glob(f"{A}/*.clm2.h0.*.nc")})
    for y in years:
        if cyc == "2" and y == "2010":   # cyc2 first year overlaps cyc1 end (redated seed)
            continue
        files = sorted(glob.glob(f"{A}/*.clm2.h0.{y}-*.nc"))
        if len(files) < 12:
            continue
        m = year_mean(files)
        seq += 1
        print("%s,%d,%s,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f" % (
            cyc, seq, y, m["FSH"], m["LH"], m["FPSN"], m["TWS"], m["H2OSOI_L8"], m["TSOI_L10"]))
