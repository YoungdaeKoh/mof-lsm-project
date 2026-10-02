#!/usr/bin/env python3
"""Noah-MP DVEG=5 carbon spin-up (6 cycles x 30 yr, WFDE5 1981-2010) -> CSV for the 4-model spin-up figure.

Values are Jan-1 03Z SNAPSHOTS (yearly RESTART + LDASOUT), not annual means:
the spin-up wrote output once a year (OUTPUT_TIMESTEP = 1 yr), so an annual-mean
GPP does not exist and is left out.  Same mask/weights as plot_dveg5_spinup.py:
non-ice land (IVGTYP not 15/17/21), cos(lat).  Soil water = SMC thickness-weighted
over the 4 layers (0.1/0.3/0.6/1.0 m) -> kg/m2 column water; deep soil T = SOIL_T
layer 4 from the LDASOUT of the same date.  Carbon gC/m2 -> kgC/m2.
Archive layout: cycleNN/RESTART.YYYY010103_DOMAIN1 (1981..2011) and
cycleNN/YYYY010103.LDASOUT_DOMAIN1.
"""
import glob
import os
import numpy as np
from netCDF4 import Dataset

A = "/Volumes/data02/NOAHMP/spinup_raw/noahmp_WFDE5_1deg_dveg5/"
SETUP = "/Volumes/data02/NOAHMP/init/HRLDAS_setup_GSWP3_1deg_d01.nc"
OUT = "/Volumes/data01/MOF_LSM_project/data/noahmp/noahmp_dveg5_spinup_jan1.csv"
DZ = np.array([0.1, 0.3, 0.6, 1.0])

with Dataset(SETUP) as s:
    lat = np.array(s.variables["XLAT"][0]); ivg = np.array(s.variables["IVGTYP"][0])
nonice = (ivg > 0) & (ivg != 17) & (ivg != 21) & (ivg != 15)
w = np.cos(np.deg2rad(lat)) * nonice


def wm(x):
    x = np.asarray(x, "f8")
    ok = np.isfinite(x) & (np.abs(x) < 1e30) & (w > 0)
    return float((x[ok] * w[ok]).sum() / w[ok].sum())


rows = []
seq = 0
for c in range(1, 7):
    for f in sorted(glob.glob(A + "cycle%02d/RESTART.????010103_DOMAIN1" % c)):
        y = int(os.path.basename(f)[8:12])
        if y == 1981 and c > 1:          # = previous cycle's 2011 state (redated seed)
            continue
        with Dataset(f) as d:
            g = {v: np.array(d.variables[v][0], "f8") for v in
                 ("LAI", "WOOD", "LFMASS", "STMASS", "RTMASS", "FASTCP", "STBLCP", "SNEQV", "SMC")}
        veg = g["LFMASS"] + g["STMASS"] + g["WOOD"] + g["RTMASS"]
        colw = (g["SMC"] * DZ[None, :, None]).sum(1) * 1000.0        # SMC is (south_north, layer, west_east)
        tdeep = np.nan
        lf = A + "cycle%02d/%d010103.LDASOUT_DOMAIN1" % (c, y)
        if not os.path.exists(lf):
            # the yearly output alarm is time based (8760 h), so after a leap year the
            # "Jan-1" file is stamped Dec-31 of the previous year (notes 9f)
            lf = A + "cycle%02d/%d123103.LDASOUT_DOMAIN1" % (c, y - 1)
        if os.path.exists(lf):
            with Dataset(lf) as d:
                st = np.array(d.variables["SOIL_T"][0], "f8")          # (y, layer, x)
                tdeep = wm(st[:, -1, :] if st.shape[1] == 4 else st[-1])
        seq += 1
        rows.append((c, y, seq, wm(g["LAI"]), wm(veg) / 1000, wm(g["FASTCP"] + g["STBLCP"]) / 1000,
                     wm(g["FASTCP"]) / 1000, wm(g["STBLCP"]) / 1000, wm(colw), tdeep, wm(g["SNEQV"])))
    print("cycle", c, "done")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as fo:
    fo.write("cycle,year,spinyear,LAI,vegC,soilC,FASTCP,STBLCP,colwater,soilT_deep,SNEQV\n")
    for r in rows:
        fo.write("%d,%d,%d," % r[:3] + ",".join("%.6g" % x for x in r[3:]) + "\n")
print("wrote", OUT, len(rows), "rows")
