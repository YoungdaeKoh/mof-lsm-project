#!/opt/homebrew/bin/python3
"""FLUXCOM-X-BASE GPP (0.5 deg monthly, yearly files, raw on data02) -> one monthly 1-degree file, 2001-2021.

Same grid as the LAI files (p1_gimms_to_monthly_1deg.py, lm4p_to_latlon.py): lat ascending
-89.5..89.5, lon -179.5..179.5, so it goes through the same NCL climatology/anomaly step.
Raw is read only (/Volumes/data02/FLUXCOM_X_BASE/GPP_monthly_0.5deg, see README.md there).
Recipe: each 1-degree cell = nanmean of its 2x2 half-degree cells (cells with no land stay missing).
Units kept as gC m-2 d-1.  Raw lat is DESCENDING -> flipped here.

Output: ../data/fluxcomx_gpp_monthly_1deg_2001_2021.nc  (gpp, time mid-month)
"""
import os
import datetime
import numpy as np
import netCDF4 as nc

RAW = "/Volumes/data02/FLUXCOM_X_BASE/GPP_monthly_0.5deg/FLUXCOM-X-BASE_GPP_monthly_0.5deg_%d.nc"
Y0, Y1 = 2001, 2021
NLAT, NLON, R = 180, 360, 2
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "fluxcomx_gpp_monthly_1deg_%d_%d.nc" % (Y0, Y1))

lat1 = -89.5 + np.arange(NLAT)
lon1 = -179.5 + np.arange(NLON)
with nc.Dataset(OUT, "w", format="NETCDF4_CLASSIC") as o:
    o.createDimension("time", None); o.createDimension("lat", NLAT); o.createDimension("lon", NLON)
    t = o.createVariable("time", "f8", ("time",)); t.units = "days since %d-01-01 00:00:00" % Y0; t.calendar = "standard"
    v = o.createVariable("lat", "f8", ("lat",)); v[:] = lat1; v.units = "degrees_north"
    v = o.createVariable("lon", "f8", ("lon",)); v[:] = lon1; v.units = "degrees_east"
    g = o.createVariable("gpp", "f4", ("time", "lat", "lon"), fill_value=1e20)
    g.units = "gC m-2 d-1"; g.long_name = "gross primary productivity (FLUXCOM-X-BASE, 2x2 block mean of 0.5 deg)"
    o.source = "poster/2026_LM4p_LAI/scripts/p2_fluxcomx_gpp_to_monthly_1deg.py"
    k = 0
    for y in range(Y0, Y1 + 1):
        with nc.Dataset(RAW % y) as d:
            la = d["lat"][:]
            assert la.size == NLAT * R and d["lon"].size == NLON * R
            a = np.ma.filled(d["GPP"][:].astype("f8"), np.nan)          # (12, 360, 720)
        if la[0] > la[-1]:
            a = a[:, ::-1, :]                                            # -> lat ascending
        with np.errstate(invalid="ignore"):
            b = np.nanmean(a.reshape(12, NLAT, R, NLON, R), axis=(2, 4))
        for m in range(12):
            t[k] = nc.date2num(datetime.datetime(y, m + 1, 16, 12), t.units, t.calendar)
            g[k] = np.where(np.isfinite(b[m]), b[m], 1e20).astype("f4")
            k += 1
        print("%d  annual mean %.3f gC m-2 d-1  valid cells %d" % (y, np.nanmean(b), np.isfinite(b[6]).sum()))
print("wrote", OUT, k, "months")
