"""Recompute the y1990 monthly land-mean LAI straight from the re-run archive.

Settles a contradiction: extract_monthly_11yr.py (local CSV) puts the annual
maximum in July, while NOTES 13.36 puts it in January.  Reads the native
land_month stream, all six tiles, and reports both an unweighted mean over the
compressed land points and a soil_area-weighted mean (lai carries
cell_measures = "area: soil_area").
"""
import numpy as np
from netCDF4 import Dataset, num2date

ARC = "/data2/ydkoh/lm4/RERUN/wA/archive/y1990"
STEM = "%s/19900101.land_month.tile%d.nc"
STATIC = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive/y1990/19900101.land_static.tile%d.nc"

num = None
den = None
wnum = None
wden = None
months = None

for t in range(1, 7):
    d = Dataset(STEM % (ARC, t))
    tv = d.variables["time"]
    mo = np.array([x.month for x in
                   num2date(tv[:], tv.units, getattr(tv, "calendar", "noleap"))])
    tb = d.variables["time_bnds"][:]
    if t == 1:
        months = mo
        print("tile1 time centres/bounds")
        for i in range(len(mo)):
            print("  rec %2d  month=%2d  bnds %.3f -> %.3f (%.1f d)"
                  % (i, mo[i], tb[i, 0], tb[i, 1], tb[i, 1] - tb[i, 0]))

    a = d.variables["lai"][:]                       # (time, grid_index), masked
    a = np.ma.masked_invalid(np.ma.filled(a.astype("f8"), np.nan))
    a = np.ma.masked_less(a, 0.0)                   # _FillValue = -1

    # soil_area weight, if the static file carries it
    try:
        s = Dataset(STATIC % t)
        w = np.ma.filled(s.variables["soil_area"][:].astype("f8"), 0.0)
        s.close()
        if w.ndim > 1:
            w = w[0]
    except Exception as e:
        w = None
        if t == 1:
            print("no soil_area (%s) -> unweighted only" % e)

    n = np.ma.filled(a.filled(0.0), 0.0).sum(axis=1)
    c = (~a.mask).sum(axis=1).astype("f8")
    num = n if num is None else num + n
    den = c if den is None else den + c

    if w is not None:
        ww = np.where(a.mask, 0.0, w[None, :])
        wnum_t = (np.ma.filled(a, 0.0) * ww).sum(axis=1)
        wden_t = ww.sum(axis=1)
        wnum = wnum_t if wnum is None else wnum + wnum_t
        wden = wden_t if wden is None else wden + wden_t
    d.close()

print("\n1990 monthly land-mean LAI (native land_month, 6 tiles)")
print(" month   unweighted   soil_area-wtd")
for i in range(len(months)):
    ww = wnum[i] / wden[i] if wnum is not None else float("nan")
    print("   %2d      %6.3f       %6.3f" % (months[i], num[i] / den[i], ww))

u = num / den
print("\nannual mean 12-month unweighted = %.4f" % u.mean())
print("annual mean Jan-Nov  unweighted = %.4f" % u[:11].mean())
print("max month = %d (%.3f)   min month = %d (%.3f)"
      % (months[u.argmax()], u.max(), months[u.argmin()], u.min()))
print("MJJAS mean = %.4f    DJF(D90,J90,F90) = %.4f"
      % (u[4:9].mean(), np.mean([u[11], u[0], u[1]])))
