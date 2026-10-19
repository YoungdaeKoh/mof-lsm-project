#!/opt/homebrew/bin/python3
"""Observed LAI at native time step -> 1-degree lat/lon, 2001-2015 (for curve fitting instead of monthly interpolation).

  glass   GLASS01B01 V61 (MODIS) 0.05 deg, 8-day composites (46/yr); recipe of poster p23 (grid-verify 2026-10-14):
          SDS "LAI" uint8 (3600,7200), row 0 = 90N, col 0 = 180W, fill 255, valid 0-100, x0.1; time = start DOY + 4
  cons    GIMMS LAI4g V1.2 consolidated, 1/12 deg, half-monthly (24/yr); recipe of poster p1; time = day 8 / day 23
  solely  GIMMS LAI4g V1.2 AVHRR-only, same
Block mean to 1 deg (nanmean of the sub-cells), lat ascending -89.5..89.5, lon -179.5..179.5 (same grid as the monthly
files), values > 100 or < 0 -> missing. Output: ../data/obs_native/<key>_1deg_2001_2015.nc (time = days since 2001-01-01)
usage: python3 o1_obs_native_to_1deg.py glass|cons|solely
"""
import glob
import os
import sys
import datetime as dt
import numpy as np
import netCDF4 as nc

KEY = sys.argv[1]
Y0, Y1 = 2001, 2015
D0 = dt.date(Y0, 1, 1)
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "obs_native")
os.makedirs(OUTDIR, exist_ok=True)
OUT = os.path.join(OUTDIR, "%s_1deg_%d_%d.nc" % (KEY, Y0, Y1))

times, fields = [], []
if KEY == "glass":
    from pyhdf.SD import SD, SDC
    SRC = "/Volumes/data02/GLASS_LAI_MODIS/%d/GLASS01B01.V61.A%d*.hdf"
    for y in range(Y0, Y1 + 1):
        files = sorted(glob.glob(SRC % (y, y)))
        for f in files:
            doy = int(os.path.basename(f)[20:23])
            s = SD(f, SDC.READ); a = s.select("LAI").get(); s.end()
            assert a.shape == (3600, 7200)
            a = np.where(a > 100, np.nan, a * 0.1)[::-1]
            with np.errstate(invalid="ignore"):
                b = np.nanmean(a.reshape(180, 20, 360, 20), axis=(1, 3))
            times.append((dt.date(y, 1, 1) - D0).days + doy - 1 + 4); fields.append(b.astype(np.float32))
        print(y, len(files), "composites", flush=True)
    src = "GLASS01B01 V61 MODIS 8-day, block mean 0.05 -> 1 deg, time = composite start DOY + 4"
else:
    VAR = "consolidated" if KEY == "cons" else "solely"
    GIM = "/Volumes/data02/LAI-DataKit/derived/gimms_lai4g/native0083/%s/GIMMS_LAI4g-%s_V1.2_" % (VAR, VAR) + "%d%02d%02d.nc"
    with nc.Dataset(GIM % (Y0, 1, 1)) as d:
        la = d.variables["lat"][:]; lat_desc = la[0] > la[-1]; assert la.size == 2160
    for y in range(Y0, Y1 + 1):
        for m in range(1, 13):
            for h, day in ((1, 8), (2, 23)):
                with nc.Dataset(GIM % (y, m, h)) as d:
                    a = np.ma.filled(d.variables["lai"][0].astype("f8"), np.nan)
                a[(a > 100) | (a < 0)] = np.nan
                with np.errstate(invalid="ignore"):
                    b = np.nanmean(a.reshape(180, 12, 360, 12), axis=(1, 3))
                b = b[::-1] if lat_desc else b
                times.append((dt.date(y, m, day) - D0).days); fields.append(b.astype(np.float32))
        print(y, "24 half-months", flush=True)
    src = "GIMMS LAI4g V1.2 %s half-monthly, block mean 1/12 -> 1 deg, time = day 8 / 23 of the month" % VAR

arr = np.stack(fields)
with nc.Dataset(OUT, "w") as d:
    d.createDimension("time", None); d.createDimension("lat", 180); d.createDimension("lon", 360)
    t = d.createVariable("time", "f8", ("time",)); t.units = "days since %d-01-01" % Y0; t.calendar = "standard"; t[:] = times
    v = d.createVariable("lat", "f8", ("lat",)); v[:] = -89.5 + np.arange(180); v.units = "degrees_north"
    v = d.createVariable("lon", "f8", ("lon",)); v[:] = -179.5 + np.arange(360); v.units = "degrees_east"
    v = d.createVariable("lai", "f4", ("time", "lat", "lon"), fill_value=np.float32(1e20), zlib=True, complevel=4)
    v.units = "m2 m-2"; v[:] = np.where(np.isfinite(arr), arr, 1e20)
    d.source = src
print("wrote", OUT, arr.shape)
