#!/usr/bin/env python3
"""Per-cell species shares of leaf area on the native C96 grid, written to a small npz for local regridding.

For every land cell: lat, lon, land area and each species' share of the July leaf area (lai by species
from land_month_by_species).  usage: python phentest_species_frac_cells.py <run_dir> <out.npz> [month_index]
"""
import glob
import os
import sys
import numpy as np
from netCDF4 import Dataset

run, out = sys.argv[1], sys.argv[2]
mon = int(sys.argv[3]) if len(sys.argv) > 3 else 6
LAT, LON, AREA, LAI = [], [], [], []
names = None
for f in sorted(glob.glob(run + "/*.land_month_by_species.tile*.nc")):
    with Dataset(f) as A:
        A.set_auto_mask(False)
        names = [s.strip() for s in A.variables["species"].species_names.split(",")]
        lai = A.variables["lai"][mon].astype("f8")
        lai = np.where((lai == getattr(A.variables["lai"], "_FillValue", -1.0)) | ~np.isfinite(lai), 0.0, lai)
        LAT.append(A.variables["geolat_t"][:].astype("f8").ravel()); LON.append(A.variables["geolon_t"][:].astype("f8").ravel())
        w = np.ones(LAT[-1].size)
        fs = f.replace("land_month_by_species", "land_static")
        if os.path.exists(fs):
            with Dataset(fs) as S:
                S.set_auto_mask(False)
                for n in ("land_area", "area_land", "soil_area"):
                    if n in S.variables:
                        w = np.squeeze(S.variables[n][:]).astype("f8").ravel(); w = np.where(w > 0, w, 0.0); break
        AREA.append(w); LAI.append(lai)
lat = np.concatenate(LAT); lon = np.concatenate(LON); area = np.concatenate(AREA); lai = np.concatenate(LAI, axis=1)
tot = lai.sum(0)
share = np.where(tot > 0, lai / np.where(tot > 0, tot, 1.0), np.nan)
np.savez(out, lat=lat, lon=np.where(lon > 180, lon - 360, lon), area=area, total_lai=tot, species=np.array(names), share=share.astype("f4"))
print("cells", lat.size, "species", names, "written", out)
