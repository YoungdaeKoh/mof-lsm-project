"""Surface (0-6 cm) volumetric soil moisture per C96 land point, MJJAS 1982-1996.

For the ESA CCI comparison.  CCI senses roughly the top 0.5-5 cm, so LM4 layers
1-2 (zhalf 0, 0.02, 0.06) are the closest match; layer 3 would take it to 10 cm.

`soil_liq` is kg/m3 (bulk density of liquid water), so dividing by 1000 gives
m3/m3.  `theta_sfc` is deliberately not used - it is a relative wetness, not a
volumetric content.

Also carries the soil-tile mask so ice cells can be dropped.

Run on climate00.  Output: /data2/ydkoh/lm4/sm_surface_1982_1996.npz
"""
import numpy as np
from netCDF4 import Dataset, num2date

RUN = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive"
RERUN = "/data2/ydkoh/lm4/RERUN/wA/archive"
STATIC = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive/y1990/19900101.land_static.tile%d.nc"
GRID = "/data2/ydkoh/lm4/RUN/lm4_spinup30/INPUT/C96_grid.tile%d.nc"
OUT = "/data2/ydkoh/lm4/sm_surface_1982_1996.npz"
YEARS = list(range(1982, 1997))
MONTHS = [5, 6, 7, 8, 9]
NX, FILL = 96, 1e19
DZ = np.array([0.02, 0.04])            # layers 1-2, 0-0.06 m

lat_all, lon_all, soil = [], [], []
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
    d = Dataset("%s/y1990/19900101.land_month.tile%d.nc" % (RERUN, t))
    a = np.ma.filled(d.variables["lai"][0].astype("f8"), np.nan)
    a[np.abs(a) > FILL] = np.nan
    d.close()
    soil.append(np.isfinite(a))
lat = np.concatenate(lat_all)
lon = np.where(np.concatenate(lon_all) > 180, np.concatenate(lon_all) - 360,
               np.concatenate(lon_all))
soil = np.concatenate(soil)
print("land %d, soil %d" % (lat.size, soil.sum()))

mod = np.full((len(YEARS), lat.size), np.nan)
for iy, y in enumerate(YEARS):
    root = RERUN if y == 1990 else RUN
    per_tile = []
    for t in range(1, 7):
        d = Dataset("%s/y%d/%d0101.land_month.tile%d.nc" % (root, y, y, t))
        tv = d.variables["time"]
        mo = np.array([x.month for x in
                       num2date(tv[:], tv.units, getattr(tv, "calendar", "noleap"))])
        a = np.ma.filled(d.variables["soil_liq"][:].astype("f8"), np.nan)
        a[np.abs(a) > FILL] = np.nan
        d.close()
        sel = np.isin(mo, MONTHS)
        v = np.einsum("k,tkp->tp", DZ, a[sel, :2, :] / 1000.0) / DZ.sum()
        per_tile.append(np.nanmean(v, axis=0))
    mod[iy] = np.concatenate(per_tile)
    print("%d  %.4f m3/m3" % (y, np.nanmean(mod[iy][soil])))

np.savez(OUT, lat=lat, lon=lon, soil=soil, years=np.array(YEARS), mod=mod)
print("wrote %s" % OUT)
