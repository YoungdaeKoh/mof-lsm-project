"""LM4 soil temperature, aggregated onto the ERA5-Land layer boundaries.

The two models do not share a soil discretisation.  LM4 carries 20 layers with
interfaces at 0, 0.02, 0.06, 0.1, 0.15, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0, 1.4, 1.8,
2.2, 2.6, 3.0, 4, 5, 6, 7.5, 10 m; ERA5-Land reports four thick layers at
0-7, 7-28, 28-100 and 100-289 cm.  Picking the nearest LM4 node to each ERA5
midpoint would compare a 2 cm slab against a 7 cm one and a 40 cm slab against a
189 cm one, which is not the same quantity -- the deeper the layer, the more the
seasonal amplitude is damped, so a mismatch in thickness shows up as a bias in
amplitude that has nothing to do with the model.

So each ERA5-Land layer is reproduced by averaging LM4's layers weighted by how
much of each falls inside it.  Layers that straddle a boundary contribute in
proportion to the overlap.

Window 1990-2010, the drift-free years (NOTES 13.46).

Run on climate00.  Output: /data2/ydkoh/lm4/soilT_era5layers_1982_2010.npz
"""
import numpy as np
from netCDF4 import Dataset, num2date

ARC = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive_c1"
RERUN = "/data2/ydkoh/lm4/RERUN/wA/archive"
STATIC = ARC + "/y1990/19900101.land_static.tile%d.nc"
GRID = "/data2/ydkoh/lm4/RUN/lm4_spinup30/INPUT/C96_grid.tile%d.nc"
OUT = "/data2/ydkoh/lm4/soilT_era5layers_1982_2010.npz"
YEARS = list(range(1982, 2011))
NX, FILL = 96, 1e19

# ERA5-Land layer interfaces, metres
ERA5_EDGES = [(0.00, 0.07), (0.07, 0.28), (0.28, 1.00), (1.00, 2.89)]

# --------------------------------------------------------------- geometry ---
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
lon = np.concatenate(lon_all)
lon = np.where(lon > 180, lon - 360, lon)

d0 = Dataset("%s/y2010/20100101.land_month.tile1.nc" % ARC)
zhalf = np.array(d0.variables["zhalf_soil"][:], "f8")
d0.close()
lm4_top, lm4_bot = zhalf[:-1], zhalf[1:]

W = np.zeros((len(ERA5_EDGES), lm4_top.size))
for k, (a, b) in enumerate(ERA5_EDGES):
    ov = np.clip(np.minimum(lm4_bot, b) - np.maximum(lm4_top, a), 0.0, None)
    W[k] = ov / ov.sum()
    used = np.nonzero(ov)[0]
    print("ERA5 layer %d (%.2f-%.2f m): LM4 layers %d-%d, weights %s"
          % (k + 1, a, b, used[0] + 1, used[-1] + 1,
             np.array2string(W[k][used], precision=3)))

# soil mask: lai rides on soil_area, so a finite lai marks non-ice land
soil = []
for t in range(1, 7):
    d = Dataset("%s/y1990/19900101.land_month.tile%d.nc" % (RERUN, t))
    a = np.ma.filled(d.variables["lai"][0].astype("f8"), np.nan)
    a[np.abs(a) > FILL] = np.nan
    d.close()
    soil.append(np.isfinite(a))
soil = np.concatenate(soil)
print("land points %d, soil %d" % (lat.size, soil.sum()))

# ------------------------------------------------------------- extraction ---
out = np.full((len(YEARS), 12, len(ERA5_EDGES), lat.size), np.nan, dtype="f4")
for iy, y in enumerate(YEARS):
    root = RERUN if y == 1990 else ARC
    per_tile = []
    for t in range(1, 7):
        d = Dataset("%s/y%d/%d0101.land_month.tile%d.nc" % (root, y, y, t))
        tv = d.variables["time"]
        mo = np.array([x.month for x in
                       num2date(tv[:], tv.units,
                                getattr(tv, "calendar", "noleap"))])
        a = np.ma.filled(d.variables["soil_T"][:].astype("f8"), np.nan)
        a[np.abs(a) > FILL] = np.nan          # (time, zfull_soil, point)
        d.close()
        slot = np.full((12, len(ERA5_EDGES), a.shape[2]), np.nan)
        for m_i, m in enumerate(mo):
            for k in range(len(ERA5_EDGES)):
                slot[m - 1, k] = np.einsum("l,lp->p", W[k], a[m_i])
        per_tile.append(slot)
    out[iy] = np.concatenate(per_tile, axis=2)
    print("%d  L1 %.2f  L4 %.2f K"
          % (y, np.nanmean(out[iy, :, 0][:, soil]), np.nanmean(out[iy, :, 3][:, soil])))

np.savez_compressed(OUT, soilT=out, lat=lat, lon=lon, soil=soil,
                    years=np.array(YEARS), months=np.arange(1, 13),
                    era5_edges=np.array(ERA5_EDGES))
print("wrote %s" % OUT)
