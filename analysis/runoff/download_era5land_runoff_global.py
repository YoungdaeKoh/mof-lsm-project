#!/usr/bin/env python3
"""
Download ERA5-Land monthly-mean runoff, GLOBAL, 0.1 deg, 1979-2023 (one file per year).
Reference (model-based, not observation) for the multi-LSM gridded-runoff diagnostics; the observational
anchor stays GRDC/UNH composite. ERA5-Land runoff comes from HTESSEL forced by ERA5 (no runoff assimilation).
Variables: runoff (ro, total), surface_runoff (sro), sub_surface_runoff (ssro).
Note: monthly_averaged_reanalysis of an accumulated field = mean daily accumulation (m of water per day).
Output: /Volumes/data02/ERA5/ERA5_Land/runoff_global/ERA5L_runoff_monthly_global_YYYY.nc
Re-runs skip years already present. Usage: python3 download_era5land_runoff_global.py [Y0 Y1]
"""
import os
import sys
import cdsapi

OUTDIR = "/Volumes/data02/ERA5/ERA5_Land/runoff_global"
Y0, Y1 = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1979, 2023)
os.makedirs(OUTDIR, exist_ok=True)
client = cdsapi.Client()
for y in range(Y0, Y1 + 1):
    out = os.path.join(OUTDIR, f"ERA5L_runoff_monthly_global_{y}.nc")
    if os.path.exists(out):
        print(f"[skip] {out}", flush=True)
        continue
    print(f"[get ] {y}", flush=True)
    client.retrieve(
        "reanalysis-era5-land-monthly-means",
        {
            "product_type":    ["monthly_averaged_reanalysis"],
            "variable":        ["runoff", "surface_runoff", "sub_surface_runoff"],
            "year":            [str(y)],
            "month":           [f"{m:02d}" for m in range(1, 13)],
            "time":            ["00:00"],
            "data_format":     "netcdf",
            "download_format": "unarchived",
        },
        out + ".part",
    )
    os.replace(out + ".part", out)   # only complete files get the final name
    print(f"[done] {out}", flush=True)
print("ALLDONE")
