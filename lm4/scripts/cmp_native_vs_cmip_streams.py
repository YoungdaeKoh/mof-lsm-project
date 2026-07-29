"""Compare native (land_month) vs CMIP (land_month_cmip) fields, same month/grid.

Checks whether the two streams differ only in value or also in mask, the way
lai does (CMIP registers with fill_missing=.TRUE.).
"""
import numpy as np, netCDF4 as nc

RUN = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive/y1995"
Y = 19950101

# (label, native var(s), cmip var)  - native tuple entries are summed
PAIRS = [
    ("LAI",          ("lai",),                    "lai"),
    ("total runoff", ("runf",),                   "mrro"),
    ("surf runoff",  ("soil_rie", "soil_rsn"),    "mrros"),
    ("soil water",   ("water_soil",),             "mrso"),
]


def read(stream, names):
    per_tile = []
    for t in range(1, 7):
        d = nc.Dataset("%s/%d.%s.tile%d.nc" % (RUN, Y, stream, t))
        acc = None
        for nm in names:
            if nm not in d.variables:
                d.close()
                return None
            v = np.ma.filled(d.variables[nm][:].astype("f8"), np.nan)
            acc = v if acc is None else acc + v
        d.close()
        per_tile.append(acc)
    a = np.concatenate(per_tile, axis=-1)
    a[a < -1e10] = np.nan
    return a


print("%-13s %10s %10s %8s %8s %8s %9s" %
      ("field", "nat mean", "cmip mean", "nat pts", "cmip pts", "corr", "diff%"))
for label, natnames, cmipname in PAIRS:
    nat = read("land_month", natnames)
    cmi = read("land_month_cmip", (cmipname,))
    if nat is None or cmi is None:
        print("%-13s  ** variable missing in one stream **" % label)
        continue
    n = np.nanmean(nat, axis=0)
    c = np.nanmean(cmi, axis=0)
    m = np.isfinite(n) & np.isfinite(c)
    corr = np.corrcoef(n[m], c[m])[0, 1] if m.sum() > 2 else np.nan
    both = 100 * (c[m].mean() - n[m].mean()) / abs(n[m].mean()) if m.sum() else np.nan
    print("%-13s %10.4g %10.4g %8d %8d %8.4f %8.2f%%   (global: %.4g vs %.4g)" %
          (label, n[m].mean(), c[m].mean(), np.isfinite(n).sum(),
           np.isfinite(c).sum(), corr, both, np.nanmean(n), np.nanmean(c)))
