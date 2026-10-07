#!/usr/bin/env python3
"""Census of vegetation cohorts by species in LM4+ restart files (vegn2.res.tile*.nc).

For each directory given: number of cohorts per species, and each species' share of the total
leaf biomass (bl x nindivs when nindivs is in the file, else bl alone).  Shows whether a species
is missing from the initial state or disappears during the run.
usage: python restart_species_census.py <dir_with_vegn2.res.tile*.nc> [<dir> ...]
"""
import glob
import os
import sys
import numpy as np
from netCDF4 import Dataset

for d in sys.argv[1:]:
    files = sorted(glob.glob(os.path.join(d, "vegn2.res.tile*.nc")))
    if not files:
        print("%s: no vegn2.res.tile*.nc" % d); continue
    names = None; cnt = None; leaf = None
    for f in files:
        with Dataset(f) as A:
            A.set_auto_mask(False)
            if names is None:
                raw = A.variables["species_names"][:]
                names = ["".join(c.decode() if isinstance(c, bytes) else str(c) for c in row).strip("\x00 ").strip() for row in raw]
                cnt = np.zeros(len(names), int); leaf = np.zeros(len(names))
            sp = A.variables["species"][:]
            bl = A.variables["bl"][:].astype("f8")
            n = A.variables["nindivs"][:].astype("f8") if "nindivs" in A.variables else np.ones(bl.size)
            ok = (sp >= 0) & (sp < len(names)) & np.isfinite(bl) & (np.abs(bl) < 1e30) & (np.abs(n) < 1e30)
            for k in range(len(names)):
                m = ok & (sp == k)
                cnt[k] += m.sum(); leaf[k] += (bl[m] * n[m]).sum()
    tot = leaf.sum()
    print(d)
    print("   " + "  ".join("%s: %d cohorts, %.1f %% of leaf biomass" % (names[k], cnt[k], 100 * leaf[k] / tot if tot > 0 else 0)
                            for k in range(len(names)) if names[k]))
