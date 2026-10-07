#!/usr/bin/env python3
"""Does each species have any leaves anywhere?  Max of lai and leaf biomass by species over
the year and all cells, and the number of cells where the species is present.
usage: python phentest_species_presence.py <run_dir>
"""
import glob
import sys
import numpy as np
from netCDF4 import Dataset

mx, cnt, names = {}, {}, None
for f in sorted(glob.glob(sys.argv[1] + "/*.land_month_by_species.tile*.nc")):
    with Dataset(f) as A:
        A.set_auto_mask(False)
        names = [s.strip() for s in A.variables["species"].species_names.split(",")]
        for v in ("lai", "bl"):
            x = A.variables[v][:].astype("f8")
            x = np.where(x == getattr(A.variables[v], "_FillValue", -1.0), 0.0, x)
            mx[v] = np.maximum(mx.get(v, 0), x.max(axis=(0, 2)))
            cnt[v] = cnt.get(v, 0) + (x.max(axis=0) > 1e-6).sum(axis=1)
print("species:", names)
for v in mx:
    print("%-3s max over the year and all cells:" % v, np.round(mx[v], 4), "| cells where present:", cnt[v])
