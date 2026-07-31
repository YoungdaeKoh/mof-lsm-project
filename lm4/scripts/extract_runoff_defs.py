"""Three definitions of "total runoff" in LM4, extracted side by side.

They are not the same quantity, and the gap is larger than the model-to-model
differences we are trying to measure:

  runf         snow_lrunf + snow_frunf + subs_lrunf   solid included, glacier
               and lake tiles included      (land_model.F90:2550)
  frunf        the frozen part of the above
  runf - frunf liquid, all tiles -- the common denominator across the four LSMs
  mrro (CMIP)  lrunf_ie + lrunf_sn + lrunf_bf + lrunf_nu   liquid only, soil
               tiles only                  (soil.F90:2996)

G-RUN is trained on gauge streamflow, so `mrro` is the matching counterpart;
using `runf` (as a first pass here did) compares a solid-plus-glacier quantity
against liquid river runoff.

Also carries the soil-tile mask so ice-sheet cells can be dropped, the same
trap that made global-mean SWE 86 % ice.

Run on climate00.  Output: /data2/ydkoh/lm4/runoff_defs_1982_1996.npz
"""
import numpy as np
from netCDF4 import Dataset, num2date

RUN = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive"
RERUN = "/data2/ydkoh/lm4/RERUN/wA/archive"
STATIC = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive/y1990/19900101.land_static.tile%d.nc"
GRID = "/data2/ydkoh/lm4/RUN/lm4_spinup30/INPUT/C96_grid.tile%d.nc"
OUT = "/data2/ydkoh/lm4/runoff_defs_1982_1996.npz"
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
lon = np.concatenate(lon_all)
lon = np.where(lon > 180, lon - 360, lon)

# soil-tile mask: lai is carried on soil_area, so a valid lai marks non-ice land
soil = []
for t in range(1, 7):
    d = Dataset("%s/y1990/19900101.land_month.tile%d.nc" % (RERUN, t))
    a = np.ma.filled(d.variables["lai"][0].astype("f8"), np.nan)
    a[np.abs(a) > FILL] = np.nan
    d.close()
    soil.append(np.isfinite(a))
soil = np.concatenate(soil)
print("land points %d, soil (non-ice) %d" % (lat.size, soil.sum()))

out = {"lat": lat, "lon": lon, "soil": soil, "years": np.array(YEARS)}
for key in ("runf", "frunf", "mrro"):
    arr = np.full((len(YEARS), lat.size), np.nan)
    for iy, y in enumerate(YEARS):
        root = RERUN if y == 1990 else RUN
        stream = "land_month_cmip" if key == "mrro" else "land_month"
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
            per_tile.append(np.nanmean(a[np.isin(mo, MONTHS)], axis=0))
        arr[iy] = np.concatenate(per_tile)
    out[key] = arr
    print("%-6s MJJAS mean  all land %.4e   soil only %.4e kg/m2/s"
          % (key, np.nanmean(arr), np.nanmean(arr[:, soil])))

liq = out["runf"] - out["frunf"]
print("%-6s MJJAS mean  all land %.4e   soil only %.4e kg/m2/s"
      % ("runf-frunf", np.nanmean(liq), np.nanmean(liq[:, soil])))
print("\nratios on soil cells:  mrro/runf %.3f   (runf-frunf)/runf %.3f"
      % (np.nanmean(out["mrro"][:, soil]) / np.nanmean(out["runf"][:, soil]),
         np.nanmean(liq[:, soil]) / np.nanmean(out["runf"][:, soil])))

np.savez(OUT, **out)
print("wrote %s" % OUT)
