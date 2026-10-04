#!/opt/homebrew/bin/python3
"""GIMMS LAI4g (1/12 deg, half-monthly) -> monthly 1-degree lat/lon NetCDF, 1982-2020.

Same grid as the LM4p lat/lon files (lm4p_to_latlon.py): lat ascending -89.5..89.5,
lon -179.5..179.5, so both go through the same NCL climatology/anomaly step.
Recipe follows lm4/scripts/lai_trend_vs_gimms.py (gimms_year): values > 100 or < 0
are missing, each half-month file is block-averaged to 1 degree (nanmean of the
12x12 sub-cells), and the two halves of a month are averaged.  netCDF4 applies
scale_factor/add_offset itself -- do NOT redo it.

Output: ../data/gimms_lai4g_monthly_1deg_1982_2020.nc  (lai, time mid-month)
"""
import os
import numpy as np
import netCDF4 as nc

GIM = ("/Users/youngdaekoh/data2/LAI-DataKit/derived/gimms_lai4g/native0083/"
       "consolidated/GIMMS_LAI4g-consolidated_V1.2_%d%02d%02d.nc")
Y0, Y1 = 1982, 2020
NLAT, NLON, R = 180, 360, 12
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "gimms_lai4g_monthly_1deg_%d_%d.nc" % (Y0, Y1))

# check the native grid orientation once (descending lat, lon -180..180 expected)
with nc.Dataset(GIM % (Y0, 1, 1)) as d:
    la, lo = d.variables["lat"][:], d.variables["lon"][:]
    print("native: lat %.4f..%.4f (%d)  lon %.4f..%.4f (%d)" % (la[0], la[-1], la.size, lo[0], lo[-1], lo.size))
    assert la.size == NLAT * R and lo.size == NLON * R
    lat_desc = la[0] > la[-1]


def half_month(y, m, h):
    with nc.Dataset(GIM % (y, m, h)) as d:
        a = np.ma.filled(d.variables["lai"][0].astype("f8"), np.nan)
    a[(a > 100) | (a < 0)] = np.nan
    with np.errstate(invalid="ignore"):
        b = np.nanmean(a.reshape(NLAT, R, NLON, R), axis=(1, 3))
    return b[::-1] if lat_desc else b                     # -> lat ascending


lat1 = -89.5 + np.arange(NLAT)
lon1 = -179.5 + np.arange(NLON)
with nc.Dataset(OUT, "w", format="NETCDF4_CLASSIC") as o:
    o.createDimension("time", None); o.createDimension("lat", NLAT); o.createDimension("lon", NLON)
    t = o.createVariable("time", "f8", ("time",)); t.units = "days since %d-01-01 00:00:00" % Y0; t.calendar = "standard"
    v = o.createVariable("lat", "f8", ("lat",)); v[:] = lat1; v.units = "degrees_north"
    v = o.createVariable("lon", "f8", ("lon",)); v[:] = lon1; v.units = "degrees_east"
    lai = o.createVariable("lai", "f4", ("time", "lat", "lon"), fill_value=1e20)
    lai.units = "m2/m2"; lai.long_name = "leaf area index (GIMMS LAI4g V1.2, monthly mean of 2 half-months, 1-deg block mean)"
    o.source = "poster/2026_LM4p_LAI/scripts/p1_gimms_to_monthly_1deg.py"
    k = 0
    for y in range(Y0, Y1 + 1):
        for m in range(1, 13):
            with np.errstate(invalid="ignore"):
                mm = np.nanmean(np.stack([half_month(y, m, 1), half_month(y, m, 2)]), axis=0)
            t[k] = nc.date2num(__import__("datetime").datetime(y, m, 16, 12), t.units, t.calendar)
            lai[k] = np.where(np.isfinite(mm), mm, 1e20).astype("f4")
            k += 1
        print("%d done  annual mean %.3f  valid cells %d" % (y, np.nanmean(np.where(lai[k - 12:k] < 1e19, lai[k - 12:k], np.nan)), np.isfinite(mm).sum()))
print("wrote", OUT, k, "months")
