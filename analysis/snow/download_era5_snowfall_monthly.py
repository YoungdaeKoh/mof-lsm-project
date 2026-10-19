#!/usr/bin/env python3
"""
Download ERA5 monthly-mean snowfall (single levels, 0.25 deg), 2001-01 ~ 2023-12, Northern Hemisphere.
Used as the observational reference for WFDE5 snowfall in the snow diagnostics
(ERA5-Land takes its precipitation from ERA5 without downscaling, so ERA5 sf ~ ERA5-Land sf).
Note: monthly_averaged_reanalysis of an accumulated field = mean daily accumulation (m w.e. per day).
Output: /Volumes/data02/ERA5/single_level/monthly_0.25/snowfall/ERA5_sf_monthly_NH_200101-202312.nc
Re-runs skip the file if present.
"""
import os
import cdsapi

OUTDIR = "/Volumes/data02/ERA5/single_level/monthly_0.25/snowfall"
OUT = os.path.join(OUTDIR, "ERA5_sf_monthly_NH_200101-202312.nc")
os.makedirs(OUTDIR, exist_ok=True)
if os.path.exists(OUT):
    print(f"[skip] exists: {OUT}")
else:
    cdsapi.Client().retrieve(
        "reanalysis-era5-single-levels-monthly-means",
        {
            "product_type":   ["monthly_averaged_reanalysis"],
            "variable":       ["snowfall"],
            "year":           [str(y) for y in range(2001, 2024)],
            "month":          [f"{m:02d}" for m in range(1, 13)],
            "time":           ["00:00"],
            "area":           [90, -180, 0, 180],   # N, W, S, E
            "data_format":    "netcdf",
            "download_format": "unarchived",
        },
        OUT,
    )
    print(f"[done] {OUT}")
