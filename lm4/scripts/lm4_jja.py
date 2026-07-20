# LM4 continuous spin-up: JJA (Jun-Jul-Aug) unweighted global-land mean per spin-up year.
# C96 quasi-equal-area -> unweighted cell mean (land_area is all-zero in this diag).
# Time decoded as gregorian 'days since 1981-01-01' -> real (year,month).
import glob, os
from datetime import datetime, timedelta
import numpy as np
from netCDF4 import Dataset

RUN = "/data2/ydkoh/lm4/RUN/lm4_wfde5_cont"
REF = datetime(1981, 1, 1)
LEV2M = 12
JJA = {6, 7, 8}

segs = sorted({os.path.basename(f).split(".land_month")[0]
               for f in glob.glob(f"{RUN}/*.land_month.tile1.nc")})

# per-year accumulators: sum and count for each variable
VARS = ["btot", "soilC", "colwater", "soilT_deep", "LAI", "nep", "sens", "evap"]
S = {v: {} for v in VARS}   # v -> {year: sum}
N = {v: {} for v in VARS}   # v -> {year: count}

def add(v, yr, arr):
    a = np.ma.masked_invalid(arr)
    S[v][yr] = S[v].get(yr, 0.0) + float(np.ma.sum(a))
    N[v][yr] = N[v].get(yr, 0.0) + int(a.count())

for seg in segs:
    for tile in range(1, 7):
        nc = Dataset(f"{RUN}/{seg}.land_month.tile{tile}.nc")
        tv = nc.variables["time"][:]
        btot = nc.variables["btot"][:]
        LAI  = nc.variables["LAI"][:]
        nep  = nc.variables["nep"][:]
        sens = nc.variables["sens"][:]
        evap = nc.variables["evap"][:]
        sT   = nc.variables["soil_T"][:, LEV2M, :]
        soilC = nc.variables["fast_soil_C"][:].sum(axis=1) + nc.variables["slow_soil_C"][:].sum(axis=1)
        colw  = nc.variables["soil_liq"][:].sum(axis=1) + nc.variables["soil_ice"][:].sum(axis=1)
        for it, t in enumerate(tv):
            d = REF + timedelta(days=float(t))
            if d.month not in JJA:
                continue
            yr = d.year
            add("btot", yr, btot[it]);   add("LAI", yr, LAI[it]);  add("nep", yr, nep[it])
            add("sens", yr, sens[it]);   add("evap", yr, evap[it]); add("soilT_deep", yr, sT[it])
            add("soilC", yr, soilC[it]); add("colwater", yr, colw[it])
        nc.close()

years = sorted(y for y in S["btot"] if N["btot"][y] > 0)
out = f"{RUN}/jja_spinup_cont.csv"
with open(out, "w") as f:
    f.write("spinup_year," + ",".join(VARS) + "\n")
    for y in years:
        vals = [S[v][y] / N[v][y] for v in VARS]
        f.write(f"{y-1980}," + ",".join(f"{x:.5g}" for x in vals) + "\n")
print(f"JJA years {years[0]-1980}-{years[-1]-1980} ({len(years)} yrs)")
for v in VARS:
    a = np.array([S[v][y]/N[v][y] for y in years])
    print(f"  {v:<11} {a[0]:.4g} -> {a[-1]:.4g}")
print("CSV:", out)
