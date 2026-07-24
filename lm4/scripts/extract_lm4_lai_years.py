"""LM4 JJA LAI per completed year (1982-1986) on C96 land points + coords.

One row per year so a multi-year mean and per-year stats can be built locally.
GIMMS starts 1982, so 1982-1986 is the matched period; 1981 is skipped to keep
the comparison apples-to-apples.
"""
import numpy as np
from netCDF4 import Dataset, num2date

RUN = "/data2/ydkoh/lm4/RUN/lm4_spinup30"
INP = RUN + "/INPUT"
YEARS = [1982, 1983, 1984, 1985, 1986]
NX = 96
FILL = 1e30

# coords are fixed (C96 land mask), recover once from the first year
lat_all, lon_all = [], []
for t in range(1, 7):
    st = Dataset("%s/archive/y%d/%d0101.land_static.tile%d.nc" % (RUN, YEARS[0], YEARS[0], t))
    gi = st.variables["grid_index"][:].astype(int)
    st.close()
    g = Dataset("%s/C96_grid.tile%d.nc" % (INP, t))
    X = g.variables["x"][:]; Y = g.variables["y"][:]; g.close()
    j = gi // NX; i = gi % NX
    lat_all.append(Y[2 * j + 1, 2 * i + 1])
    lon_all.append(X[2 * j + 1, 2 * i + 1])
lat = np.concatenate(lat_all)
lon = np.concatenate(lon_all)
lon = np.where(lon > 180, lon - 360, lon)

out = {"lat": lat, "lon": lon, "years": np.array(YEARS)}
for y in YEARS:
    per_tile = []
    for t in range(1, 7):
        d = Dataset("%s/archive/y%d/%d0101.land_month.tile%d.nc" % (RUN, y, y, t))
        tv = d.variables["time"]
        months = np.array([dt.month for dt in
                           num2date(tv[:], tv.units, getattr(tv, "calendar", "noleap"))])
        jja = np.isin(months, [6, 7, 8])
        a = np.ma.filled(d.variables["lai"][:].astype("f8"), np.nan)
        a[np.abs(a) > FILL] = np.nan
        per_tile.append(np.nanmean(a[jja, :], axis=0))
        d.close()
    lai = np.concatenate(per_tile)
    out["lai_%d" % y] = lai
    v = lai[np.isfinite(lai)]
    print("%d JJA LAI mean=%.3f" % (y, v.mean()))

np.savez(RUN + "/lm4_lai_jja_1982_1986.npz", **out)
print("wrote lm4_lai_jja_1982_1986.npz  (%d cells x %d years)" % (len(lat), len(YEARS)))
