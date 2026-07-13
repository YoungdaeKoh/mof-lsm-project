#!/usr/bin/env python
# LM4 full 300-yr spin-up, ANNUAL resolution, from each segment's land_annual (FMS annual
# means). 9 segments x 29 yr = ~261 annual points; the 91-120 segment (y120) was not archived
# (only the IC_static_120yr milestone survives) -> a gap there. Cumulative spin-up year assigned
# from each segment's end-year. Soil water 0.70 m, soil temp 1.20 m, column water. 6 tiles.
import glob
import numpy as np
from netCDF4 import Dataset

BASE = "/data2/ydkoh/lm4"
SEG = [("RUN/lm4_backfill", 30), ("spinup_raw/y60recov", 60), ("spinup_raw/y90recov", 90),
       ("spinup_raw/y150", 150), ("spinup_raw/y180", 180), ("spinup_raw/y210", 210),
       ("spinup_raw/y240", 240), ("spinup_raw/y270", 270), ("spinup_raw/y300", 300)]
IWATER, ITEMP = 8, 10
zf = np.array([0.01,0.04,0.08,0.125,0.175,0.25,0.35,0.50,0.70,0.90,1.20,1.60,2.00,2.40,2.80,3.50,4.50,5.50,6.75,8.75])
edges = np.concatenate([[0], (zf[:-1]+zf[1:])/2, [zf[-1]+(zf[-1]-zf[-2])/2]])
dz = np.diff(edges)

def lm(a):
    a = a[np.isfinite(a) & (np.abs(a) < 1e10)]; return float(a.mean())

print("year,SW_070,ST_120,colwater,NEP")
for sub, end in SEG:
    tiles = {}
    for t in range(1, 7):
        fs = glob.glob(f"{BASE}/{sub}/*.land_annual.tile{t}.nc")
        if not fs:
            tiles = None; break
        d = Dataset(fs[0]); d.set_auto_mask(False)
        tiles[t-1] = {"T": d.variables["soil_T"][:].astype("f8"),
                      "sw": (d.variables["soil_liq"][:] + d.variables["soil_ice"][:]).astype("f8"),
                      "nep": d.variables["nep"][:].astype("f8")}
        d.close()
    if tiles is None:
        continue
    nt = tiles[0]["T"].shape[0]                       # 29
    for i in range(nt):
        cumyr = end - nt + i                          # end-29 .. end-1
        sw = np.concatenate([tiles[t]["sw"][i, IWATER, :] for t in range(6)])
        st = np.concatenate([tiles[t]["T"][i, ITEMP, :] for t in range(6)])
        col = np.concatenate([np.nansum(np.where(np.abs(tiles[t]["sw"][i]) < 1e10,
                  tiles[t]["sw"][i] * dz[:, None], np.nan), axis=0) for t in range(6)])
        nep = np.concatenate([tiles[t]["nep"][i, :] for t in range(6)])
        print("%d,%.5f,%.4f,%.3f,%.6f" % (cumyr, lm(sw), lm(st), lm(col), lm(nep)))
