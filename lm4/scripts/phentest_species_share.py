#!/usr/bin/env python3
"""Where does each LM4+ species live?  Share of leaf area by species, July, by latitude band and region.

Reads lai by species from land_month_by_species on the native C96 tiles (land_area weights
from land_static when present).  Regions are simple lon-lat boxes that approximate the AR6
regions used on the poster (exact polygons need regionmask, which the server lacks).
usage: python phentest_species_share.py <run_dir> [month_index, default 6 = July]
"""
import glob
import os
import sys
import numpy as np
from netCDF4 import Dataset

run = sys.argv[1]
mon = int(sys.argv[2]) if len(sys.argv) > 2 else 6
BOX = [("70-90N", 70, 90, -180, 180), ("50-70N", 50, 70, -180, 180), ("30-50N", 30, 50, -180, 180),
       ("0-30N", 0, 30, -180, 180), ("60S-0", -60, 0, -180, 180),
       ("NWN box 50-72N 168-105W", 50, 72, -168, -105), ("ESB 45-65N 90-130E", 45, 65, 90, 130),
       ("RFE box 45-65N 130-180E", 45, 65, 130, 180), ("ENA box 25-50N 90-60W", 25, 50, -90, -60),
       ("WCE box 45-61N 10W-40E", 45, 61, -10, 40), ("EAS box 20-45N 100-145E", 20, 45, 100, 145)]
names = None
acc = np.zeros((len(BOX), 16)); area = np.zeros(len(BOX))
for f in sorted(glob.glob(run + "/*.land_month_by_species.tile*.nc")):
    with Dataset(f) as A:
        A.set_auto_mask(False)
        if names is None:
            names = [s.strip() for s in A.variables["species"].species_names.split(",")]
        lai = A.variables["lai"][mon].astype("f8")            # (species, grid_index)
        fill = getattr(A.variables["lai"], "_FillValue", -1.0)
        lat = A.variables["geolat_t"][:].astype("f8").ravel(); lon = A.variables["geolon_t"][:].astype("f8").ravel()
        lon = np.where(lon > 180, lon - 360, lon)
        w = np.ones(lat.size)
        fs = f.replace("land_month_by_species", "land_static")
        if os.path.exists(fs):
            with Dataset(fs) as S:
                S.set_auto_mask(False)
                for n in ("land_area", "area_land", "soil_area"):
                    if n in S.variables:
                        w = np.squeeze(S.variables[n][:]).astype("f8").ravel(); w = np.where(w > 0, w, 0.0); break
        lai = np.where((lai == fill) | ~np.isfinite(lai), 0.0, lai)
        for i, (_, a, b, x0, x1) in enumerate(BOX):
            m = (lat >= a) & (lat < b) & (lon >= x0) & (lon < x1)
            acc[i, :lai.shape[0]] += (lai[:, m] * w[m]).sum(1); area[i] += w[m].sum()
ns = len(names)
print("share of %s leaf area by species (%%), run %s; last column = mean total LAI" % (["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][mon], os.path.basename(run)))
print("%-26s " % "region" + " ".join("%8s" % n for n in names) + "   LAI")
for i, (lab, *_r) in enumerate(BOX):
    tot = acc[i, :ns].sum()
    print("%-26s " % lab + " ".join("%8.1f" % (100 * acc[i, k] / tot if tot > 0 else 0) for k in range(ns)) + "  %5.2f" % (tot / area[i] if area[i] > 0 else 0))
