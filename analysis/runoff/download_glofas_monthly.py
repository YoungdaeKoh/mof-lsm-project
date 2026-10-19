#!/usr/bin/env python3
"""
GloFAS historical (ERA5-forced LISFLOOD) river discharge, GLOBAL 0.05 deg, reduced to MONTHLY means on the fly.
Source: EWDS (not CDS) dataset cems-glofas-historical, system_version v4.0 (operational), consolidated,
        variable average_river_discharge_in_the_last_24_hours (daily, m3/s), timespan time_mean.
For each month: request the month's daily fields -> monthly mean (+ number of valid days) -> delete the daily file.
Output: /Volumes/data02/runoff/GloFAS_v4/monthly/glofas_v4_dis24_mon_YYYYMM.nc   (daily kept only with KEEPDAILY=1)
Usage: python3 download_glofas_monthly.py Y0 Y1        (re-runs skip finished months)
Licence: CEMS-FLOODS datasets licence (accepted by the user on EWDS, 2026-10-08).
"""
import os, re, sys, time
import numpy as np, xarray as xr
import ecmwf.datastores as ed

OUT = "/Volumes/data02/runoff/GloFAS_v4"
Y0, Y1 = int(sys.argv[1]), int(sys.argv[2])
os.makedirs(OUT + "/monthly", exist_ok=True); os.makedirs(OUT + "/tmp_daily", exist_ok=True)
key = re.search(r"key:\s*(\S+)", open(os.path.expanduser("~/.cdsapirc")).read()).group(1)
client = ed.Client(url="https://ewds.climate.copernicus.eu/api", key=key)

for y in range(Y0, Y1 + 1):
    for m in range(1, 13):
        mon = OUT + f"/monthly/glofas_v4_dis24_mon_{y}{m:02d}.nc"
        if os.path.exists(mon):
            print(f"[skip] {y}-{m:02d}", flush=True); continue
        nd = (np.datetime64(f"{y + (m == 12)}-{(m % 12) + 1:02d}-01") - np.datetime64(f"{y}-{m:02d}-01")).astype(int)
        daily = OUT + f"/tmp_daily/glofas_v4_dis24_day_{y}{m:02d}.nc"
        t0 = time.time()
        if not os.path.exists(daily):
            client.retrieve("cems-glofas-historical", {
                "system_version": ["version_4_0"], "hydrological_model": ["lisflood"],
                "product_type": ["consolidated"], "timespan": ["time_mean"],
                "variable": ["average_river_discharge_in_the_last_24_hours"],
                "year": [str(y)], "month": [f"{m:02d}"], "day": [f"{d:02d}" for d in range(1, nd + 1)],
                "data_format": "netcdf", "download_format": "unarchived"}, daily + ".part")
            os.replace(daily + ".part", daily)
        sz = os.path.getsize(daily) / 1e6
        ds = xr.open_dataset(daily)
        v = [k for k in ds.data_vars if ds[k].ndim == 3][0]
        tdim = [d for d in ds[v].dims if "time" in d][0]
        da = ds[v]
        out = xr.Dataset({"dis24": da.mean(tdim, keep_attrs=True).astype("f4"),
                          "ndays": da.notnull().sum(tdim).astype("i2")})
        out["dis24"].attrs.update(units=da.attrs.get("units", "m3 s-1"),
                                  long_name="monthly mean of GloFAS v4 24-h mean river discharge")
        out = out.expand_dims(time=[np.datetime64(f"{y}-{m:02d}-15")])
        out.attrs.update(source="EWDS cems-glofas-historical v4.0 consolidated, daily dis24 averaged by month",
                         ndays_in_request=int(ds[tdim].size), script="analysis/runoff/download_glofas_monthly.py")
        enc = {"dis24": {"zlib": True, "complevel": 4}, "ndays": {"zlib": True, "complevel": 4}}
        out.to_netcdf(mon + ".part", encoding=enc); os.replace(mon + ".part", mon)
        ds.close()
        if os.environ.get("KEEPDAILY") != "1":
            os.remove(daily)
        print(f"[done] {y}-{m:02d}: var {v}, days {ds[tdim].size}/{nd}, daily {sz:.0f} MB, "
              f"monthly {os.path.getsize(mon)/1e6:.0f} MB, {time.time()-t0:.0f} s", flush=True)
print("ALLDONE")
