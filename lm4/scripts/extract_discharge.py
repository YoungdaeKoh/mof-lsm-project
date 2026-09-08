"""River discharge at the mouth, from the production run, with coordinates.

The river fields live on the structured 96x96 cubed-sphere tiles and carry
grid_xt/grid_yt as bare indices, so coordinates have to come from C96_grid --
the same corner arrays the LAI extraction uses, sampled at cell centres.

Two quantities are kept because they answer different questions:
  rv_Qavg  m3/s        river flow through the cell, directly comparable to a
                       gauge reading
  dis_liq  kg/m2/s     liquid freshwater leaving the land for the ocean, which
                       is the quantity the ocean model actually receives

Before any of it is used, the mapping is checked the only way that means
anything: the largest discharge in the world had better be the Amazon.  A
cubed-sphere field with coordinates attached the wrong way round would still
produce a plausible-looking global mean.

Window 1979-2023, all 45 production years.

Run on climate00.  Output: /data2/ydkoh/lm4/discharge_1979_2023.npz
"""
import numpy as np
from netCDF4 import Dataset, num2date

ARC = "/data2/ydkoh/lm4/RUN/lm4p_ctl_1979-2024/archive"
GRID = "/data2/ydkoh/lm4/RUN/lm4_spinup30/INPUT/C96_grid.tile%d.nc"
OUT = "/data2/ydkoh/lm4/discharge_1979_2023.npz"
YEARS = list(range(1979, 2024))
FILL = 1e19

# ---- coordinates of the 96x96 cell centres, per tile ------------------------
lat, lon, area = [], [], []
for t in range(1, 7):
    g = Dataset(GRID % t)
    X, Y = g.variables["x"][:], g.variables["y"][:]
    g.close()
    lat.append(np.array(Y[1::2, 1::2], "f8"))
    lon.append(np.array(X[1::2, 1::2], "f8"))
    d = Dataset("%s/y2010/20100101.river_month.tile%d.nc" % (ARC, t))
    area.append(np.ma.filled(d.variables["cell_area"][:].astype("f8"), np.nan))
    d.close()
lat = np.stack(lat)                      # (6, 96, 96)
lon = np.where(np.stack(lon) > 180, np.stack(lon) - 360, np.stack(lon))
area = np.stack(area)
print("grid: %s   lat %.1f..%.1f   lon %.1f..%.1f"
      % (str(lat.shape), lat.min(), lat.max(), lon.min(), lon.max()))

# ---- read both fields for every year ---------------------------------------
nQ = np.full((len(YEARS), 12, 6, 96, 96), np.nan, dtype="f4")
nD = np.full((len(YEARS), 12, 6, 96, 96), np.nan, dtype="f4")
for iy, y in enumerate(YEARS):
    for t in range(1, 7):
        d = Dataset("%s/y%d/%d0101.river_month.tile%d.nc" % (ARC, y, y, t))
        tv = d.variables["time"]
        mo = np.array([x.month for x in
                       num2date(tv[:], tv.units,
                                getattr(tv, "calendar", "noleap"))])
        for name, arr in (("rv_Qavg", nQ), ("dis_liq", nD)):
            a = np.ma.filled(d.variables[name][:].astype("f8"), np.nan)
            a[np.abs(a) > FILL] = np.nan
            for k, m in enumerate(mo):
                arr[iy, m - 1, t - 1] = a[k]
        d.close()
    if y % 10 == 0 or y == YEARS[0]:
        print("  %d" % y)

# ---- the check that matters -------------------------------------------------
qm = np.nanmean(nQ, axis=(0, 1))                      # (6,96,96) annual mean m3/s
k = np.unravel_index(np.nanargmax(qm), qm.shape)
print("\nlargest mean river flow: %.0f m3/s at %.1fN %.1fE"
      % (qm[k], lat[k], lon[k]))
print("  (the Amazon mouth is near 0.5S 50W and carries ~200,000 m3/s)")
top = np.argsort(qm.ravel())[::-1][:8]
print("\n%-8s %8s %8s %12s" % ("rank", "lat", "lon", "m3/s"))
for r, i in enumerate(top, 1):
    j = np.unravel_index(i, qm.shape)
    print("%-8d %8.1f %8.1f %12.0f" % (r, lat[j], lon[j], qm[j]))

np.savez_compressed(OUT, rv_Qavg=nQ, dis_liq=nD, lat=lat, lon=lon,
                    cell_area=area, years=np.array(YEARS),
                    months=np.arange(1, 13))
print("\nwrote %s" % OUT)
