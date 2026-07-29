"""Compare native (land_month) vs CMIP (land_month_cmip) LAI, same month/grid."""
import numpy as np, netCDF4 as nc
RUN = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive/y1995"
Y = 19950101
nat, cmi = [], []
for t in range(1, 7):
    a = nc.Dataset("%s/%d.land_month.tile%d.nc" % (RUN, Y, t))
    b = nc.Dataset("%s/%d.land_month_cmip.tile%d.nc" % (RUN, Y, t))
    nat.append(np.ma.filled(a.variables["lai"][:].astype("f8"), np.nan))
    cmi.append(np.ma.filled(b.variables["lai"][:].astype("f8"), np.nan))
    a.close(); b.close()
nat = np.concatenate(nat, axis=-1); cmi = np.concatenate(cmi, axis=-1)
print("shape native=%s cmip=%s" % (nat.shape, cmi.shape))
nat[nat < -1e10] = np.nan; cmi[cmi < -1e10] = np.nan
for name, v in (("native", nat), ("cmip", cmi)):
    print("%-7s months=%d  land cells=%d  ann-mean=%.4f  min=%.3f max=%.3f"
          % (name, v.shape[0], np.isfinite(v[0]).sum(), np.nanmean(v),
             np.nanmin(v), np.nanmax(v)))
# same-cell comparison on the annual mean
n = np.nanmean(nat, axis=0); c = np.nanmean(cmi, axis=0)
m = np.isfinite(n) & np.isfinite(c)
print("\nn=%d cells both valid" % m.sum())
print("mean native=%.4f  mean cmip=%.4f  diff(cmip-native)=%+.4f (%.1f%%)"
      % (n[m].mean(), c[m].mean(), c[m].mean()-n[m].mean(),
         100*(c[m].mean()-n[m].mean())/n[m].mean()))
print("corr=%.4f  max|diff|=%.3f" % (np.corrcoef(n[m], c[m])[0, 1],
                                     np.abs(c[m]-n[m]).max()))
r = c[m]/np.where(n[m] > 0.01, n[m], np.nan)
print("ratio cmip/native: median=%.4f  p5=%.4f  p95=%.4f"
      % (np.nanmedian(r), np.nanpercentile(r, 5), np.nanpercentile(r, 95)))
