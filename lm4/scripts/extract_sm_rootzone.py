"""Root-zone (0-1 m) volumetric soil moisture, LM4+ vs ERA5-Land, MJJAS 1982-1996.

The depths line up exactly, which is why this is the layer worth comparing:
  LM4    zhalf 0, .02, .06, .1, .15, .2, .3, .4, .6, .8, 1.0  -> layers 1-10 = 0-1 m
  ERA5   swvl1 0-0.07, swvl2 0.07-0.28, swvl3 0.28-1.00       -> 0-1 m

Units matter here.  LM4 `soil_liq` is kg/m3 (bulk density of liquid water), so
dividing by 1000 gives m3/m3.  `theta_sfc` is NOT usable for this: it is
"relative soil wetness", a saturation fraction, not a volumetric content, and
comparing it against swvl would be a units error.

ERA5 files are packed shorts; netCDF4 unpacks them itself, so no manual
scale_factor (the mistake that once turned GIMMS LAI into 0.002).

Writes MJJAS per-year fields on the common 1-degree grid for both.
"""
import numpy as np
from netCDF4 import Dataset

E5 = "/data2/ydkoh/ERA5-land/volumetric_soil_water/monthly/ERA5m_%04d%02d.nc"
RUN = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive"
RERUN = "/data2/ydkoh/lm4/RERUN/wA/archive"
STATIC = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive/y1990/19900101.land_static.tile%d.nc"
GRID = "/data2/ydkoh/lm4/RUN/lm4_spinup30/INPUT/C96_grid.tile%d.nc"
OUT = "/data2/ydkoh/lm4/sm_rootzone_1982_1996.npz"
YEARS = list(range(1982, 1997))
MONTHS = [5, 6, 7, 8, 9]
NX, FILL = 96, 1e19
NLAT, NLON = 180, 360

# LM4 layer thicknesses down to 1 m
ZH = np.array([0, .02, .06, .10, .15, .20, .30, .40, .60, .80, 1.00])
DZ = np.diff(ZH)                      # 10 values, sums to 1.0
# ERA5 layer thicknesses to 1 m
E5DZ = np.array([0.07, 0.21, 0.72])

# ----------------------------------------------------------------- ERA5 -----
d = Dataset(E5 % (1990, 7))
elat = np.array(d.variables["latitude"][:], "f8")
elon = np.array(d.variables["longitude"][:], "f8")
print("ERA5 grid: lat %d %.2f..%.2f (%s)   lon %d %.2f..%.2f"
      % (elat.size, elat[0], elat[-1], "desc" if elat[0] > elat[-1] else "asc",
         elon.size, elon[0], elon[-1]))
a = d.variables["swvl1"][0]
print("  swvl1 auto-unpacked: min %.4f max %.4f mean %.4f  valid %.1f %%"
      % (a.min(), a.max(), a.mean(), 100 * (1 - np.ma.getmaskarray(a).mean())))
d.close()

# target 1-degree grid, lat descending 89.5 .. -89.5 (same as the LAI figures)
lat1 = 89.5 - np.arange(NLAT)
lon1 = -179.5 + np.arange(NLON)
# ERA5 here is 1 deg on integer nodes (181 lats): nearest node per target centre
jj = np.array([np.abs(elat - v).argmin() for v in lat1])
elon180 = np.where(elon > 180, elon - 360, elon)
ii = np.array([np.abs(elon180 - v).argmin() for v in lon1])

era = np.full((len(YEARS), NLAT, NLON), np.nan)
for iy, y in enumerate(YEARS):
    acc = None
    for m in MONTHS:
        d = Dataset(E5 % (y, m))
        s = None
        for k, nm in enumerate(("swvl1", "swvl2", "swvl3")):
            v = np.ma.filled(d.variables[nm][0].astype("f8"), np.nan)
            s = v * E5DZ[k] if s is None else s + v * E5DZ[k]
        d.close()
        acc = s if acc is None else acc + s
    era[iy] = (acc / len(MONTHS))[np.ix_(jj, ii)]      # depth-weighted 0-1 m
print("ERA5 MJJAS rootzone: mean %.4f m3/m3" % np.nanmean(era))

# ----------------------------------------------------------------- LM4 ------
lat_all, lon_all, keepmask = [], [], []
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
mlat = np.concatenate(lat_all)
mlon = np.concatenate(lon_all)
mlon = np.where(mlon > 180, mlon - 360, mlon)

mod = np.full((len(YEARS), mlat.size), np.nan)
for iy, y in enumerate(YEARS):
    root = RERUN if y == 1990 else RUN
    per_tile = []
    for t in range(1, 7):
        d = Dataset("%s/y%d/%d0101.land_month.tile%d.nc" % (root, y, y, t))
        tv = d.variables["time"]
        from netCDF4 import num2date
        mo = np.array([x.month for x in
                       num2date(tv[:], tv.units, getattr(tv, "calendar", "noleap"))])
        a = np.ma.filled(d.variables["soil_liq"][:].astype("f8"), np.nan)
        a[np.abs(a) > FILL] = np.nan
        d.close()
        sel = np.isin(mo, MONTHS)
        # kg/m3 -> m3/m3, depth-weighted over 0-1 m
        v = np.einsum("k,tkp->tp", DZ, a[sel, :10, :] / 1000.0) / DZ.sum()
        per_tile.append(np.nanmean(v, axis=0))
    mod[iy] = np.concatenate(per_tile)
print("LM4 MJJAS rootzone: mean %.4f m3/m3" % np.nanmean(mod))

np.savez(OUT, lat=mlat, lon=mlon, years=np.array(YEARS),
         mod=mod, era=era, lat1=lat1, lon1=lon1)
print("wrote %s" % OUT)
