"""Monthly runoff on the C96 land points, 1990-2010, three definitions.

extract_runoff_defs.py took an MJJAS mean, which is enough to score a summer
map and not enough for anything to do with the Arctic: high-latitude runoff is
a spring pulse, and how much freshwater reaches the ocean is an annual total.
So keep all twelve months and aggregate later.

The window starts at 1990 because 1982-89 is spin-up drift (NOTES 13.46).

Definitions, none of which is interchangeable with another (13.50, and the
runoff-definition note):
  runf         solid included, glacier and lake tiles included
  frunf        the frozen part of runf
  mrro (CMIP)  liquid only, soil tiles only -- the counterpart to gauge-trained
               products like G-RUN

Run on climate00.  Output: /data2/ydkoh/lm4/runoff_monthly_1990_2010.npz
"""
import numpy as np
from netCDF4 import Dataset, num2date

ARC = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive_c1"
RERUN = "/data2/ydkoh/lm4/RERUN/wA/archive"
STATIC = ARC + "/y1990/19900101.land_static.tile%d.nc"
GRID = "/data2/ydkoh/lm4/RUN/lm4_spinup30/INPUT/C96_grid.tile%d.nc"
OUT = "/data2/ydkoh/lm4/runoff_monthly_1990_2010.npz"
YEARS = list(range(1990, 2011))
NX, FILL = 96, 1e19

lat_all, lon_all, area_all = [], [], []
for t in range(1, 7):
    st = Dataset(STATIC % t)
    gi = st.variables["grid_index"][:].astype(int)
    # land_area is what turns a flux density into a volume; without it an
    # Arctic discharge number is meaningless
    area_all.append(np.ma.filled(st.variables["land_area"][:].astype("f8"), np.nan))
    st.close()
    g = Dataset(GRID % t)
    X, Y = g.variables["x"][:], g.variables["y"][:]
    g.close()
    j, i = gi // NX, gi % NX
    lat_all.append(Y[1::2, 1::2][j, i])
    lon_all.append(X[1::2, 1::2][j, i])
lat = np.concatenate(lat_all)
lon = np.concatenate(lon_all)
area = np.concatenate(area_all)
lon = np.where(lon > 180, lon - 360, lon)

# soil-tile mask: lai rides on soil_area, so a finite lai marks non-ice land
soil = []
for t in range(1, 7):
    d = Dataset("%s/y1990/19900101.land_month.tile%d.nc" % (RERUN, t))
    a = np.ma.filled(d.variables["lai"][0].astype("f8"), np.nan)
    a[np.abs(a) > FILL] = np.nan
    d.close()
    soil.append(np.isfinite(a))
soil = np.concatenate(soil)
print("land points %d, soil (non-ice) %d, land area %.4e m2"
      % (lat.size, soil.sum(), np.nansum(area)))

out = {"lat": lat, "lon": lon, "soil": soil, "area": area,
       "years": np.array(YEARS), "months": np.arange(1, 13)}

for key in ("runf", "frunf", "mrro"):
    stream = "land_month_cmip" if key == "mrro" else "land_month"
    arr = np.full((len(YEARS), 12, lat.size), np.nan, dtype="f4")
    for iy, y in enumerate(YEARS):
        root = RERUN if y == 1990 else ARC
        per_tile = []
        for t in range(1, 7):
            d = Dataset("%s/y%d/%d0101.%s.tile%d.nc" % (root, y, y, stream, t))
            tv = d.variables["time"]
            mo = np.array([x.month for x in
                           num2date(tv[:], tv.units,
                                    getattr(tv, "calendar", "noleap"))])
            a = np.ma.filled(d.variables[key][:].astype("f8"), np.nan)
            a[np.abs(a) > FILL] = np.nan
            d.close()
            # 1990 is the re-run and has twelve; 1991-1996 stop at November, so
            # place each record by its own month rather than by position
            slot = np.full((12, a.shape[1]), np.nan)
            for k, m in enumerate(mo):
                slot[m - 1] = a[k]
            per_tile.append(slot)
        arr[iy] = np.concatenate(per_tile, axis=1)
        nmo = np.isfinite(arr[iy]).any(axis=1).sum()
        if nmo != 12:
            print("  %d: only %d months" % (y, nmo))
    out[key] = arr
    ann = np.nanmean(arr, axis=1)
    print("%-6s annual mean, soil cells: %.4e kg/m2/s" % (key, np.nanmean(ann[:, soil])))

np.savez_compressed(OUT, **out)
print("wrote %s" % OUT)
