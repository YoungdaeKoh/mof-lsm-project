"""Are the variables the year-one diagnostics need actually being written?

The chain's guard 4 checks that twelve monthly records exist and that the six
tiles are combined, which catches the failures that have happened before.  It
does not look inside the file.  A stream can carry twelve records of _FillValue
and pass.

So this reads the fields each diagnostic axis depends on and reports, per
variable, how many of the twelve months are present, what fraction of the land
points are finite, and the annual mean over the non-ice land the diagnostics
actually use.  Values are compared against the same quantity in cycle 1, which is
the only reference available while the production run is still going.

Run on climate00.
"""
import sys
import numpy as np
from netCDF4 import Dataset, num2date

PROD = "/data2/ydkoh/lm4/RUN/lm4p_ctl_1979-2024/archive"
CYC1 = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive_c1"
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 1995
FILL = 1e19

# variable, stream, what it feeds
VARS = [
    ("lai",        "land_month",      "vegetation"),
    ("gpp",        "land_month",      "vegetation"),
    ("bwood",      "land_month",      "vegetation (carbon)"),
    ("tot_soil_C", "land_month",      "carbon"),
    ("soil_T",     "land_month",      "soil temperature"),
    ("water_soil", "land_month",      "soil moisture"),
    ("soil_liq",   "land_month",      "soil moisture"),
    ("runf",       "land_month",      "runoff"),
    ("frunf",      "land_month",      "runoff (solid)"),
    ("soil_rbf",   "land_month",      "runoff (baseflow)"),
    ("evap_land",  "land_month",      "energy / water"),
    ("sens",       "land_month",      "energy"),
    ("snow",       "land_month",      "snow"),
    ("precip",     "land_month",      "forcing check"),
    ("mrro",       "land_month_cmip", "runoff (CMIP)"),
    ("mrros",      "land_month_cmip", "runoff (CMIP surface)"),
    ("dis_liq",    "river_month",     "discharge to ocean"),
]

# non-ice soil mask, from cycle 1 (same grid, same land)
soil = []
for t in range(1, 7):
    d = Dataset("%s/y1990/19900101.land_month.tile%d.nc" % (CYC1, t))
    a = np.ma.filled(d.variables["lai"][0].astype("f8"), np.nan)
    a[np.abs(a) > FILL] = np.nan
    d.close()
    soil.append(np.isfinite(a))
soil = np.concatenate(soil)
print("non-ice soil points: %d\n" % soil.sum())


def read(root, year, stream, var):
    per, months = [], None
    for t in range(1, 7):
        f = "%s/y%d/%d0101.%s.tile%d.nc" % (root, year, year, stream, t)
        d = Dataset(f)
        tv = d.variables["time"]
        months = np.array([x.month for x in
                           num2date(tv[:], tv.units,
                                    getattr(tv, "calendar", "noleap"))])
        a = np.ma.filled(d.variables[var][:].astype("f8"), np.nan)
        a[np.abs(a) > FILL] = np.nan
        d.close()
        if a.ndim == 3 and stream != "river_month":     # (time, layer, point)
            a = a[:, 12, :] if a.shape[1] > 12 else a.mean(axis=1)
        per.append(a)
    axis = 1 if per[0].ndim == 2 else None
    return (np.concatenate(per, axis=axis) if axis else np.stack(per)), months


print("%-12s %-17s %7s %9s %14s %14s %8s" %
      ("variable", "feeds", "months", "finite%", "prod %d" % YEAR,
       "cycle1 1995", "ratio"))
for var, stream, feeds in VARS:
    try:
        a, mo = read(PROD, YEAR, stream, var)
    except Exception as e:
        print("%-12s %-17s  READ FAILED: %s" % (var, feeds, str(e)[:40]))
        continue

    if stream == "river_month":                 # (tile, time, y, x)
        vals = a
        fin = 100.0 * np.isfinite(vals).mean()
        m_prod = np.nanmean(vals)
    else:
        vals = np.where(soil[None, :], a, np.nan)
        fin = 100.0 * np.isfinite(vals).mean()
        m_prod = np.nanmean(vals)

    try:
        b, _ = read(CYC1, 1995, stream, var)
        m_c1 = np.nanmean(b if stream == "river_month"
                          else np.where(soil[None, :], b, np.nan))
        ratio = "%.3f" % (m_prod / m_c1) if m_c1 else "-"
    except Exception:
        m_c1, ratio = float("nan"), "n/a"

    flag = "" if (len(mo) == 12 and fin > 1 and np.isfinite(m_prod)) else "   <-- CHECK"
    print("%-12s %-17s %7d %8.1f%% %14.5g %14.5g %8s%s"
          % (var, feeds, len(mo), fin, m_prod, m_c1, ratio, flag))
