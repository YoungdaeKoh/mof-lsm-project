"""Confirm the re-run actually produced a complete December."""
import netCDF4 as nc, numpy as np
f = "/data2/ydkoh/lm4/RERUN/wA/archive/y1990/19900101.land_month.tile1.nc"
d = nc.Dataset(f)
t = d.variables["time"]; cal = getattr(t, "calendar", "standard")
dts = nc.num2date(t[:], t.units, calendar=cal)
b = d.variables["time_bnds"][:]
print("records = %d   calendar = %s" % (len(dts), cal))
for i in (0, len(dts) - 2, len(dts) - 1):
    bd = nc.num2date(b[i], t.units, calendar=cal)
    print("  [%2d] centre %s   window %s -> %s"
          % (i, dts[i].strftime("%Y-%m-%d %H:%M"),
             bd[0].strftime("%Y-%m-%d %H:%M"), bd[1].strftime("%Y-%m-%d %H:%M")))
lai = np.ma.filled(d.variables["lai"][:].astype("f8"), np.nan)
lai[lai < -1e10] = np.nan
print("\nmonthly land-mean LAI:")
print("  " + "  ".join("%s=%.3f" % (dts[i].strftime("%b"), np.nanmean(lai[i]))
                       for i in range(len(dts))))
d.close()
