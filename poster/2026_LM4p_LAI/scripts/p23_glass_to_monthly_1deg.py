#!/opt/homebrew/bin/python3
"""GLASS LAI V61 (MODIS, GLASS01B01, 0.05 deg, 8-day) -> monthly 1-degree lat/lon NetCDF, 2001-2020.

Same grid and recipe as p1_gimms_to_monthly_1deg.py (GIMMS LAI4g): lat ascending -89.5..89.5, lon -179.5..179.5,
each composite block-averaged to 1 degree (nanmean of the 20x20 sub-cells), composites assigned to the month of their
centre day (start DOY + 4) and averaged within the month.
Native grid (grid-verify 2026-10-14, raw-array plot = whole globe, north up): SDS "LAI" uint8 (3600, 7200),
row 0 = 90N (descending), col 0 = 180W, _FillValue 255, valid_range 0-100, scale_factor 0.1 (pyhdf does not apply it).
Output: ../data/glass_lai_modis_monthly_1deg_2001_2020.nc (lai, time mid-month)
"""
import glob
import os
import datetime as dt
import numpy as np
import netCDF4 as nc
from pyhdf.SD import SD, SDC

SRC = "/Volumes/data02/GLASS_LAI_MODIS/%d/GLASS01B01.V61.A%d*.hdf"
Y0, Y1 = 2001, 2020
R = 20
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "glass_lai_modis_monthly_1deg_%d_%d.nc" % (Y0, Y1))

out = np.full(((Y1 - Y0 + 1) * 12, 180, 360), np.nan, np.float32)
for y in range(Y0, Y1 + 1):
    acc = np.zeros((12, 180, 360)); cnt = np.zeros((12, 180, 360))
    files = sorted(glob.glob(SRC % (y, y)))
    for f in files:
        doy = int(os.path.basename(f)[20:23])
        m = (dt.date(y, 1, 1) + dt.timedelta(doy - 1 + 4)).month - 1
        if (dt.date(y, 1, 1) + dt.timedelta(doy - 1 + 4)).year != y:
            continue                                   # centre day falls in the next year
        s = SD(f, SDC.READ); a = s.select("LAI").get(); s.end()
        assert a.shape == (3600, 7200)
        a = np.where(a > 100, np.nan, a * 0.1)[::-1]   # fill/out-of-range -> NaN, flip to lat ascending
        b = np.nanmean(a.reshape(180, R, 360, R), axis=(1, 3))
        ok = np.isfinite(b)
        acc[m][ok] += b[ok]; cnt[m][ok] += 1
    out[(y - Y0) * 12:(y - Y0 + 1) * 12] = np.where(cnt > 0, acc / np.maximum(cnt, 1), np.nan)
    print(y, len(files), "files; composites per month", cnt.max(axis=(1, 2)).astype(int).tolist(), flush=True)

with nc.Dataset(OUT, "w") as d:
    d.createDimension("time", None); d.createDimension("lat", 180); d.createDimension("lon", 360)
    t = d.createVariable("time", "f8", ("time",)); t.units = "days since 1900-01-01"; t.calendar = "standard"
    t[:] = [(dt.date(y, mm, 15) - dt.date(1900, 1, 1)).days for y in range(Y0, Y1 + 1) for mm in range(1, 13)]
    la = d.createVariable("lat", "f8", ("lat",)); la[:] = -89.5 + np.arange(180); la.units = "degrees_north"
    lo = d.createVariable("lon", "f8", ("lon",)); lo[:] = -179.5 + np.arange(360); lo.units = "degrees_east"
    v = d.createVariable("lai", "f4", ("time", "lat", "lon"), fill_value=np.float32(1e20)); v.units = "m2 m-2"
    v[:] = np.where(np.isfinite(out), out, 1e20)
    d.source = "GLASS01B01 V61 (MODIS) 0.05 deg 8-day, block mean to 1 deg, monthly by composite centre day"
print("wrote", OUT)
