"""Check the first WFDE5-forced land output is physical, not just non-crashing.

C96 is quasi-equal-area so an unweighted cell mean is close to an area mean
(see the land-mean comparability note); values here are global land means.
"""
import glob
import numpy as np
import netCDF4 as nc

R = "/data2/ydkoh/lm4/RUN/lm4_offline_probe"
files = sorted(glob.glob("%s/19810101.land_daily.tile*.nc" % R))
print("tiles:", len(files))

d0 = nc.Dataset(files[0])
cands = ["temp", "t_ref", "evap", "sens", "lwup", "swdn", "precip",
         "soil_T", "soil_water", "LAI", "npp", "gpp", "runf"]
avail = [v for v in cands if v in d0.variables]
print("checked vars:", avail)
d0.close()

for v in avail:
    vals = []
    for f in files:
        d = nc.Dataset(f)
        a = np.ma.filled(d.variables[v][:].astype("f8"), np.nan); a[a > 1e30] = np.nan
        vals.append(a.ravel())
        units = getattr(d.variables[v], "units", "-")
        d.close()
    a = np.concatenate(vals)
    fin = np.isfinite(a)
    if fin.sum() == 0:
        print("%-12s ALL MISSING" % v)
        continue
    g = a[fin]
    print("%-12s mean=%11.4g  min=%11.4g  max=%11.4g  n=%d  NaN=%d  units=%s" % (
        v, g.mean(), g.min(), g.max(), fin.sum(), (~fin).sum(), units))
