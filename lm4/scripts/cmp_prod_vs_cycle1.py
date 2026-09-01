"""Production run against cycle 1, year by year over the thirty years they share.

The earlier check compared a single year and left the question half answered: are
the two runs close because the model is insensitive to where it started, or do
they only happen to agree in 1995?  Both cover 1981-2010 with the same model, the
same configuration and the same WFDE5 forcing, differing only in initial state --
cycle 1 began from the KIOST equilibrium in 1981, the production run from cycle
1's own 2010 state with the clock wound back to 1979 -- so the year-by-year
difference is a direct measure of how long that difference survives.

What the shape of the curve means:
  narrowing   the initial-condition difference is being washed out; the variable
              is equilibrated and the two runs are converging on one trajectory
  flat        a persistent offset, which for a pool means the two runs sit at
              different levels and neither is moving
  widening    the variable is not in equilibrium and the runs are drifting apart

Means are over non-ice soil points, unweighted on the C96 grid, which is nearly
equal-area, so this is comparable between the two runs even though it would not
be comparable against another model.

Run on climate00.  Output: /data2/ydkoh/lm4/cmp_prod_vs_cycle1.csv
"""
import numpy as np
from netCDF4 import Dataset, num2date

PROD = "/data2/ydkoh/lm4/RUN/lm4p_ctl_1979-2024/archive"
CYC1 = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive_c1"
RERUN = "/data2/ydkoh/lm4/RERUN/wA/archive"
OUT = "/data2/ydkoh/lm4/cmp_prod_vs_cycle1.csv"
YEARS = list(range(1981, 2011))
FILL = 1e19

VARS = [("lai", "land_month"), ("gpp", "land_month"),
        ("bwood", "land_month"), ("tot_soil_C", "land_month"),
        ("soil_T", "land_month"), ("water_soil", "land_month"),
        ("runf", "land_month"), ("evap_land", "land_month"),
        ("sens", "land_month"), ("snow", "land_month"),
        ("precip", "land_month")]

soil = []
for t in range(1, 7):
    d = Dataset("%s/y1990/19900101.land_month.tile%d.nc" % (RERUN, t))
    a = np.ma.filled(d.variables["lai"][0].astype("f8"), np.nan)
    a[np.abs(a) > FILL] = np.nan
    d.close()
    soil.append(np.isfinite(a))
soil = np.concatenate(soil)


def annual(root, year, stream, var):
    """Jan-Nov mean: cycle 1 has no December before 1997, so that is the window
    both runs share for every year."""
    per = []
    for t in range(1, 7):
        d = Dataset("%s/y%d/%d0101.%s.tile%d.nc" % (root, year, year, stream, t))
        tv = d.variables["time"]
        mo = np.array([x.month for x in
                       num2date(tv[:], tv.units,
                                getattr(tv, "calendar", "noleap"))])
        a = np.ma.filled(d.variables[var][:].astype("f8"), np.nan)
        a[np.abs(a) > FILL] = np.nan
        d.close()
        if a.ndim == 3:
            a = a[:, 12, :]                     # soil_T: the ~2 m layer
        per.append(np.nanmean(a[mo <= 11], axis=0))
    v = np.concatenate(per)
    return np.nanmean(v[soil])


rows = []
print("Jan-Nov means over non-ice soil, production / cycle 1\n")
hdr = "%-6s" % "year" + "".join("%12s" % v for v, _ in VARS)
print(hdr)
for y in YEARS:
    line = []
    for var, stream in VARS:
        try:
            p = annual(PROD, y, stream, var)
            c = annual(RERUN if y == 1990 else CYC1, y, stream, var)
            line.append(p / c if c else np.nan)
        except Exception:
            line.append(np.nan)
    rows.append([y] + line)
    print("%-6d" % y + "".join("%12.4f" % v for v in line))

r = np.array(rows)
print("\n%-14s %10s %10s %10s %10s" %
      ("variable", "1981", "1995", "2010", "trend %/decade"))
for k, (var, _) in enumerate(VARS, start=1):
    col = r[:, k]
    ok = np.isfinite(col)
    if ok.sum() < 5:
        continue
    slope = np.polyfit(r[ok, 0], col[ok], 1)[0] * 10 * 100
    print("%-14s %10.4f %10.4f %10.4f %+10.2f" %
          (var, col[0], col[r[:, 0] == 1995][0], col[-1], slope))

np.savetxt(OUT, r, delimiter=",",
           header="year," + ",".join(v for v, _ in VARS), comments="", fmt="%.6f")
print("\nwrote %s" % OUT)
