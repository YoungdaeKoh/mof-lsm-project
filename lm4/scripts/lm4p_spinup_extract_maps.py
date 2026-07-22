"""Annual-mean spatial fields (1982) + recovered C96 coords, for mapping.

Reuses the proven grid_index -> supergrid-center recovery (lm4/scripts/
lm4_coords.py, notes 13.6). Values come straight from land_month (already
correct); only the coordinates need reconstructing because geolat/geolon are
zero in this diag. Writes one npz with per-cell lat/lon and annual-mean fields.
"""
import numpy as np
from netCDF4 import Dataset

RUN = "/data2/ydkoh/lm4/RUN/lm4_spinup30"
ARCH = RUN + "/archive/y1982"
INP = RUN + "/INPUT"
NX = 96
FILL = 1e30

FIELDS = {"LAI": ("lai", None), "runoff": ("frunf", None),
          "evap": ("evap_land", None), "theta_sfc": ("theta_sfc", None),
          "sens": ("sens", None), "soilT_2m": ("soil_T", 12)}

lat_all, lon_all = [], []
vals = {k: [] for k in FIELDS}

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
    for k, (var, layer) in FIELDS.items():
        a = np.ma.filled(d.variables[var][:].astype("f8"), np.nan)
        a[np.abs(a) > FILL] = np.nan
        if layer is not None:
            a = a[:, layer, :]              # (months, grid_index)
        vals[k].append(np.nanmean(a, axis=0))   # annual mean over the 11-12 months
    d.close()

lat = np.concatenate(lat_all)
lon = np.concatenate(lon_all)
lon = np.where(lon > 180, lon - 360, lon)

out = {"lat": lat, "lon": lon}
for k in FIELDS:
    out[k] = np.concatenate(vals[k])

np.savez(RUN + "/maps_1982.npz", **out)
print("cells=%d  lat[%.1f,%.1f]  lon[%.1f,%.1f]" % (
    len(lat), lat.min(), lat.max(), lon.min(), lon.max()))
for k in FIELDS:
    v = out[k]
    v = v[np.isfinite(v)]
    print("  %-10s mean=%.4g  [%.4g, %.4g]" % (k, v.mean(), v.min(), v.max()))
# latitudinal sanity for LAI (tropics should exceed poles)
for band, (a, b) in {"NH high": (55, 90), "tropics": (-15, 15),
                     "SH high": (-60, -30)}.items():
    m = (lat >= a) & (lat < b) & np.isfinite(out["LAI"])
    if m.sum():
        print("  LAI %s: %.2f (n=%d)" % (band, np.nanmean(out["LAI"][m]), m.sum()))
