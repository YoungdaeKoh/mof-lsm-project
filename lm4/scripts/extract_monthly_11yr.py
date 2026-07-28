"""Global land-mean monthly time series over all completed LM4 years.

Same unweighted C96 cell mean as the 2-year version, but loops every archived
year so the full trajectory is visible. Each year file holds Jan-Nov (Dec is
dropped by the 364d21h segment end); the time axis is decoded per file so gaps
are handled honestly. Emits a CSV with a real decimal-year column.
"""
import glob
import os
import numpy as np
from netCDF4 import Dataset, num2date

RUN = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive"
TILES = [1, 2, 3, 4, 5, 6]
FILL = 1e30

years = sorted(int(os.path.basename(d)[1:])
               for d in glob.glob(RUN + "/y[0-9]*"))
print("years:", years)

VARS = {
    "runoff":    ("runf", None),        # TOTAL runoff (not frunf!)
    "baseflow":  ("soil_rbf", None),
    "LAI":       ("lai", None),
    "GPP":       ("gpp", None),
    "NPP":       ("npp", None),
    "NEP":       ("nep", None),
    "evap":      ("evap_land", None),
    "sens":      ("sens", None),
    "theta_sfc": ("theta_sfc", None),
    "col_water": ("water_soil", None),
    "SWE":       ("snow", None),
    "soilC":     ("tot_soil_C", None),
    "bwood":     ("bwood", None),
    "soilT_2m":  ("soil_T", 12),
}

rows = []          # (decimal_year, {var: value})
for y in years:
    # read months + per-var tile-summed means for this year
    # accumulate over tiles: sum and count per month
    acc = {k: [None, None] for k in VARS}   # [sum, count] arrays over months
    months = None
    for t in TILES:
        f = "%s/y%d/%d0101.land_month.tile%d.nc" % (RUN, y, y, t)
        d = Dataset(f)
        tv = d.variables["time"]
        mo = np.array([dt.month for dt in
                       num2date(tv[:], tv.units, getattr(tv, "calendar", "noleap"))])
        months = mo
        for k, (var, layer) in VARS.items():
            a = np.ma.filled(d.variables[var][:].astype("f8"), np.nan)
            a[np.abs(a) > FILL] = np.nan
            if layer is not None:
                a = a[:, layer, :]
            s = np.nansum(a, axis=1)
            c = np.sum(np.isfinite(a), axis=1).astype("f8")
            acc[k][0] = s if acc[k][0] is None else acc[k][0] + s
            acc[k][1] = c if acc[k][1] is None else acc[k][1] + c
        d.close()
    for i, m in enumerate(months):
        dec = y + (m - 0.5) / 12.0
        row = {"year": dec}
        for k in VARS:
            s, c = acc[k]
            row[k] = s[i] / c[i] if c[i] > 0 else np.nan
        rows.append(row)

cols = ["year"] + list(VARS.keys())
data = np.array([[r[c] for c in cols] for r in rows])
out = RUN + "/../monthly_11yr.csv"
np.savetxt(out, data, delimiter=",", header=",".join(cols), comments="")
print("wrote %s  (%d months)" % (out, len(rows)))
# annual means for the slow-pool trend check
print("\nyear  LAI   soilC  bwood  colwater  runoff(mm/d)")
for y in years:
    m = [r for r in rows if int(r["year"]) == y]
    lai = np.nanmean([r["LAI"] for r in m])
    sc = np.nanmean([r["soilC"] for r in m])
    bw = np.nanmean([r["bwood"] for r in m])
    cw = np.nanmean([r["col_water"] for r in m])
    ro = np.nanmean([r["runoff"] for r in m]) * 86400
    print("%d  %.3f  %.3f  %.3f  %.0f  %.3f" % (y, lai, sc, bw, cw, ro))
