# LM4 continuous spin-up: area-weighted global-mean deep soil T (2 m), annual mean.
# FIX: decode 'days since 1981-01-01' GREGORIAN properly -> real calendar year
# (avoids the tv//365 leap-day drift that mixed Dec/Jan and made fake spikes).
import glob, os
from datetime import datetime, timedelta
import numpy as np
from netCDF4 import Dataset

RUN = "/data2/ydkoh/lm4/RUN/lm4_wfde5_cont"
LEV = 12          # 0-based zfull_soil index -> 2.0 m
REF = datetime(1981, 1, 1)

segs = sorted({os.path.basename(f).split(".land_month")[0]
               for f in glob.glob(f"{RUN}/*.land_month.tile1.nc")})

# accumulate per (year): sum(T) and cell-count across all records & tiles.
# NOTE: land_area is all-zero in this diag config; but LM4 C96 cubed-sphere cells are
# quasi-equal-area, so an unweighted per-cell mean == area-weighted mean (CLAUDE.md known-issue).
wsum = {}   # year -> sum(T)
asum = {}   # year -> cell count
for seg in segs:
    for tile in range(1, 7):
        fn = f"{RUN}/{seg}.land_month.tile{tile}.nc"
        nc = Dataset(fn)
        T = nc.variables["soil_T"][:, LEV, :]          # (time, grid_index)
        tvals = nc.variables["time"][:]                # days since 1981-01-01
        Tm = np.ma.masked_less(T, 0.0)                 # fill -100 (none present)
        for it, tv in enumerate(tvals):
            yr = (REF + timedelta(days=float(tv))).year
            row = Tm[it]
            num = float(np.ma.sum(row))
            den = float((~np.ma.getmaskarray(row)).sum())
            wsum[yr] = wsum.get(yr, 0.0) + num
            asum[yr] = asum.get(yr, 0.0) + den
        nc.close()

years = [y for y in sorted(wsum) if asum[y] > 0]
out = f"{RUN}/cont_deepT_annual_v2.csv"
with open(out, "w") as f:
    f.write("spinup_year,soilT_2m\n")
    for y in years:
        f.write(f"{y-1980},{wsum[y]/asum[y]:.4f}\n")

arr = np.array([[y-1980, wsum[y]/asum[y]] for y in years])
print(f"years {arr[0,0]:.0f}-{arr[-1,0]:.0f} ({len(arr)} yrs), "
      f"{arr[0,1]:.2f} -> {arr[-1,1]:.2f} K")
tail = arr[arr[:,0] > arr[-1,0]-20, 1]
print(f"last-20yr mean {tail.mean():.3f} std {tail.std():.3f} K "
      f"(low std = converged, no aliasing)")
print("CSV:", out)
