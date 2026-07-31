"""MJJAS total runoff per C96 land point, 1982-1996, for the G-RUN comparison.

`runf` is total runoff in kg/(m2 s); the plotting script converts to mm/day.
y1990 comes from the re-run, every other year from the main chain.

Run on climate00.  Output: /data2/ydkoh/lm4/runoff_1982_1996.npz
"""
import numpy as np
from netCDF4 import Dataset, num2date

RUN = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive"
RERUN = "/data2/ydkoh/lm4/RERUN/wA/archive"
STATIC = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive/y1990/19900101.land_static.tile%d.nc"
GRID = "/data2/ydkoh/lm4/RUN/lm4_spinup30/INPUT/C96_grid.tile%d.nc"
OUT = "/data2/ydkoh/lm4/runoff_1982_1996.npz"
YEARS = list(range(1982, 1997))
MONTHS = [5, 6, 7, 8, 9]
NX, FILL = 96, 1e19

lat_all, lon_all = [], []
for t in range(1, 7):
    st = Dataset(STATIC % t)
    gi = st.variables["grid_index"][:].astype(int)
    st.close()
    g = Dataset(GRID % t)
    X, Y = g.variables["x"][:], g.variables["y"][:]
    g.close()
    j, i = gi // NX, gi % NX
    lat_all.append(Y[1::2, 1::2][j, i])
    lon_all.append(X[1::2, 1::2][j, i])
lat = np.concatenate(lat_all)
lon = np.where(np.concatenate(lon_all) > 180, np.concatenate(lon_all) - 360,
               np.concatenate(lon_all))

mod = np.full((len(YEARS), lat.size), np.nan)
for iy, y in enumerate(YEARS):
    root = RERUN if y == 1990 else RUN
    per_tile = []
    for t in range(1, 7):
        d = Dataset("%s/y%d/%d0101.land_month.tile%d.nc" % (root, y, y, t))
        tv = d.variables["time"]
        mo = np.array([x.month for x in
                       num2date(tv[:], tv.units, getattr(tv, "calendar", "noleap"))])
        a = np.ma.filled(d.variables["runf"][:].astype("f8"), np.nan)
        a[np.abs(a) > FILL] = np.nan
        d.close()
        per_tile.append(np.nanmean(a[np.isin(mo, MONTHS)], axis=0))
    mod[iy] = np.concatenate(per_tile)
    print("%d  %.6f kg/m2/s" % (y, np.nanmean(mod[iy])))

np.savez(OUT, lat=lat, lon=lon, years=np.array(YEARS), mod=mod)
print("wrote %s" % OUT)
