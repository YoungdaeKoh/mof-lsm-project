"""LM4 LAI JJA 1982 mean on C96 land points + recovered coords -> npz.

land_month is missing January (segment starts 03:00), so pick Jun/Jul/Aug by
decoding the time axis rather than by fixed index.
"""
import numpy as np
from netCDF4 import Dataset, num2date

RUN = "/data2/ydkoh/lm4/RUN/lm4_spinup30"
ARCH = RUN + "/archive/y1982"
INP = RUN + "/INPUT"
NX = 96
FILL = 1e30

lat_all, lon_all, lai_all = [], [], []
for t in range(1, 7):
    st = Dataset("%s/19820101.land_static.tile%d.nc" % (ARCH, t))
    gi = st.variables["grid_index"][:].astype(int)
    st.close()
    g = Dataset("%s/C96_grid.tile%d.nc" % (INP, t))
    X = g.variables["x"][:]
    Y = g.variables["y"][:]
    g.close()
    j = gi // NX
    i = gi % NX
    lat_all.append(Y[2 * j + 1, 2 * i + 1])
    lon_all.append(X[2 * j + 1, 2 * i + 1])

    d = Dataset("%s/19820101.land_month.tile%d.nc" % (ARCH, t))
    tv = d.variables["time"]
    dates = num2date(tv[:], tv.units,
                     getattr(tv, "calendar", "noleap"))
    months = np.array([dt.month for dt in dates])
    jja = np.isin(months, [6, 7, 8])
    if t == 1:
        print("months present:", sorted(set(months.tolist())),
              "| JJA records:", int(jja.sum()))
    a = np.ma.filled(d.variables["lai"][:].astype("f8"), np.nan)
    a[np.abs(a) > FILL] = np.nan
    lai_all.append(np.nanmean(a[jja, :], axis=0))
    d.close()

lat = np.concatenate(lat_all)
lon = np.concatenate(lon_all)
lon = np.where(lon > 180, lon - 360, lon)
lai = np.concatenate(lai_all)

np.savez(RUN + "/lm4_lai_jja1982.npz", lat=lat, lon=lon, lai=lai)
v = lai[np.isfinite(lai)]
print("cells=%d  LAI JJA mean=%.3f [%.3f, %.3f]" % (len(lat), v.mean(), v.min(), v.max()))
