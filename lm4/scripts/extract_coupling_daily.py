"""Daily MJJAS soil moisture and evapotranspiration for the terrestrial coupling leg.

Full land-atmosphere coupling (Mi, lambda) needs the atmospheric response and is
therefore a coupled-run job, as the project's variable plan already states.  What
an offline run gives cleanly is the terrestrial leg -- soil moisture controlling
evapotranspiration -- and it gives it without the confounding feedback, since
the atmosphere here cannot respond.

Per cell and per day over MJJAS 1982-1996 this accumulates the sums needed for
  rho(SM, ET)             correlation
  dET/dSM                 regression slope
  sigma(SM) x dET/dSM     Dirmeyer-style terrestrial coupling index
computed on daily anomalies about each year's MJJAS mean, so the seasonal march
does not manufacture a correlation.

SM is root-zone 0-1 m from soil_liq (kg/m3 -> m3/m3); ET is evap_land.
Only the running sums are carried home, not the daily fields.

Run on climate00.  Output: /data2/ydkoh/lm4/coupling_daily_1982_1996.npz
"""
import numpy as np
from netCDF4 import Dataset, num2date

RUN = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive"
RERUN = "/data2/ydkoh/lm4/RERUN/wA/archive"
STATIC = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive/y1990/19900101.land_static.tile%d.nc"
GRID = "/data2/ydkoh/lm4/RUN/lm4_spinup30/INPUT/C96_grid.tile%d.nc"
OUT = "/data2/ydkoh/lm4/coupling_daily_1982_1996.npz"
YEARS = list(range(1982, 1997))
NX, FILL = 96, 1e19
ZH = np.array([0, .02, .06, .10, .15, .20, .30, .40, .60, .80, 1.00])
DZ = np.diff(ZH)

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
npts = lat.size
print("land %d, soil %d" % (npts, soil.sum()))

n = np.zeros(npts)
sxx = np.zeros(npts)
syy = np.zeros(npts)
sxy = np.zeros(npts)
smean = np.zeros(npts)
emean = np.zeros(npts)
nyr = 0

for y in YEARS:
    root = RERUN if y == 1990 else RUN
    sm_t, et_t = [], []
    for t in range(1, 7):
        d = Dataset("%s/y%d/%d0101.land_daily.tile%d.nc" % (root, y, y, t))
        tv = d.variables["time"]
        mo = np.array([x.month for x in
                       num2date(tv[:], tv.units, getattr(tv, "calendar", "noleap"))])
        sel = (mo >= 5) & (mo <= 9)
        liq = np.ma.filled(d.variables["soil_liq"][sel].astype("f8"), np.nan)
        liq[np.abs(liq) > FILL] = np.nan
        nz = min(liq.shape[1], DZ.size)
        sm = np.einsum("k,tkp->tp", DZ[:nz], liq[:, :nz, :] / 1000.0) / DZ[:nz].sum()
        ev = np.ma.filled(d.variables["evap_land"][sel].astype("f8"), np.nan)
        ev[np.abs(ev) > FILL] = np.nan
        d.close()
        sm_t.append(sm)
        et_t.append(ev)
    sm = np.concatenate(sm_t, axis=1)
    et = np.concatenate(et_t, axis=1)
    # anomalies about this year's MJJAS mean, so the seasonal march is removed
    a = sm - np.nanmean(sm, axis=0)
    b = et - np.nanmean(et, axis=0)
    ok = np.isfinite(a) & np.isfinite(b)
    n += ok.sum(axis=0)
    sxx += np.nansum(np.where(ok, a * a, 0), axis=0)
    syy += np.nansum(np.where(ok, b * b, 0), axis=0)
    sxy += np.nansum(np.where(ok, a * b, 0), axis=0)
    smean += np.nanmean(sm, axis=0)
    emean += np.nanmean(et, axis=0)
    nyr += 1
    print("%d  %d days, mean SM %.4f  ET %.3e" % (y, sm.shape[0],
                                                  np.nanmean(sm[:, soil]),
                                                  np.nanmean(et[:, soil])))

np.savez(OUT, lat=lat, lon=lon, soil=soil, n=n, sxx=sxx, syy=syy, sxy=sxy,
         sm_mean=smean / nyr, et_mean=emean / nyr, nyr=nyr)
print("wrote %s" % OUT)
