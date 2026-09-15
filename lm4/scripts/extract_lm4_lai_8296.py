"""LM4 LAI per year 1982-2023 on the C96 land points, with coordinates.

History: written for cycle 1 (lm4_spinup30, 1982-2010 -- hence "8296" in the
file name, kept so that NOTES 13.3x references still resolve).  Since 2026-09
it reads the production run lm4p_ctl_1979-2024 instead, which has every year
1982-2023 complete, and YEARS/OUT below reflect that.

Two aggregations per year so the observed comparison can be run either way:
  ann  = Jan-Nov mean  (a cycle-1 constraint: 1997-2010 had a December and 1990
                        did too, but 1982-1996 did not, so Jan-Nov was the only
                        window all years shared.  The production run has every
                        December, but the window is kept so that "ann" means
                        the same thing across both runs and in the notes.)
  mjjas = May-Sep mean (northern growing season, contains the annual maximum)

Coordinates come from C96_grid corner arrays via grid_index, the same recipe as
extract_lm4_lai_years.py.  Saved as npz so the intermediate survives this time
(NOTES 13.26 lost the previous one to a working directory).
"""
import numpy as np
from netCDF4 import Dataset
from netCDF4 import num2date
from greenland_mask import in_greenland

RUN = "/data2/ydkoh/lm4/RUN/lm4_spinup30"
# cycle 1 was moved aside to archive_c1 when the 1979-2024 production run took
# over the archive/ name; this script reads the finished cycle, not the new one.
ARC = "/data2/ydkoh/lm4/RUN/lm4p_ctl_1979-2024/archive"
RERUN = "/data2/ydkoh/lm4/RERUN/wA/archive"
INP = RUN + "/INPUT"
YEARS = list(range(1982, 2024))
NX = 96
FILL = 1e30
OUT = "/data2/ydkoh/lm4/lm4_lai_1982_2023.npz"

lat_all, lon_all = [], []
for t in range(1, 7):
    st = Dataset("%s/y1990/19900101.land_static.tile%d.nc" % (ARC, t))
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
lat = np.concatenate(lat_all)
lon = np.concatenate(lon_all)
lon = np.where(lon > 180, lon - 360, lon)
print("C96 land points: %d   lat %.1f..%.1f" % (lat.size, lat.min(), lat.max()))

# Greenland removed by its Natural Earth outline -- same mask as the time series
keep = ~in_greenland(lat, lon)
print("after Greenland cut: %d" % keep.sum())

out = {"lat": lat, "lon": lon, "keep": keep, "years": np.array(YEARS)}
for y in YEARS:
    root = ARC          # production run has every year; no re-run substitution
    ann, mjj = [], []
    for t in range(1, 7):
        d = Dataset("%s/y%d/%d0101.land_month.tile%d.nc" % (root, y, y, t))
        tv = d.variables["time"]
        mo = np.array([x.month for x in
                       num2date(tv[:], tv.units, getattr(tv, "calendar", "noleap"))])
        a = np.ma.filled(d.variables["lai"][:].astype("f8"), np.nan)
        a[np.abs(a) > FILL] = np.nan
        ann.append(np.nanmean(a[(mo >= 1) & (mo <= 11), :], axis=0))
        mjj.append(np.nanmean(a[(mo >= 5) & (mo <= 9), :], axis=0))
        d.close()
    out["ann_%d" % y] = np.concatenate(ann)
    out["mjjas_%d" % y] = np.concatenate(mjj)
    print("%d  ann=%.4f  mjjas=%.4f"
          % (y, np.nanmean(out["ann_%d" % y][keep]),
             np.nanmean(out["mjjas_%d" % y][keep])))

np.savez(OUT, **out)
print("wrote %s" % OUT)
