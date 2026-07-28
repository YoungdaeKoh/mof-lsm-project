"""grid-verify one datakit GIMMS file before use."""
import glob
import numpy as np
import netCDF4 as nc

f = sorted(glob.glob("/Users/youngdaekoh/data2/LAI-DataKit/derived/gimms_lai4g/"
                     "native0083/consolidated/*.nc"))
print("consolidated files:", len(f))
d = nc.Dataset(f[0])
print("file:", f[0].split("/")[-1])
print("vars:", list(d.variables.keys()))
print("dims:", {k: len(v) for k, v in d.dimensions.items()})
for c in ("lat", "latitude", "lon", "longitude", "time"):
    if c in d.variables:
        v = d.variables[c][:]
        print("%-10s n=%d  %.4f -> %.4f  d=%.5f" % (
            c, len(v), float(v[0]), float(v[-1]), float(v[1] - v[0])))
# find LAI var
for lv in ("lai", "LAI", "LAI4g"):
    if lv in d.variables:
        a = d.variables[lv]
        print("LAI var '%s' shape=%s units=%s fill=%s" % (
            lv, a.shape, getattr(a, "units", "-"), getattr(a, "_FillValue", "-")))
        arr = np.ma.filled(a[:].astype("f8"), np.nan)
        arr[arr > 100] = np.nan
        g = arr[np.isfinite(arr)]
        print("  valid %.1f%%  min=%.3f max=%.3f mean=%.3f" % (
            100 * np.isfinite(arr).mean(), g.min(), g.max(), g.mean()))
d.close()
