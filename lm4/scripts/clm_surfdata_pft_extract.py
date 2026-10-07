#!/usr/bin/env python3
"""Extract the PFT fractions from a CLM5 surface dataset into a small file for local analysis.

Writes pct_pft(natpft, lat, lon) = PCT_NAT_PFT * PCT_NATVEG / 100 (percent of the grid cell),
pct_crop, landfrac, lat, lon (as stored: LATIXY/LONGXY), without touching the original.
usage: python clm_surfdata_pft_extract.py <surfdata.nc> <out.nc>
"""
import sys
import numpy as np
from netCDF4 import Dataset

with Dataset(sys.argv[1]) as A, Dataset(sys.argv[2], "w") as O:
    A.set_auto_mask(False)
    lat = A.variables["LATIXY"][:, 0]; lon = A.variables["LONGXY"][0, :]
    nat = A.variables["PCT_NATVEG"][:]; pft = A.variables["PCT_NAT_PFT"][:]
    O.createDimension("natpft", pft.shape[0]); O.createDimension("lat", lat.size); O.createDimension("lon", lon.size)
    for n, v in (("lat", lat), ("lon", lon)):
        O.createVariable(n, "f8", (n,))[:] = v
    x = O.createVariable("pct_pft", "f4", ("natpft", "lat", "lon"), zlib=True)
    x[:] = pft * nat[None] / 100.0
    x.long_name = "PFT area as percent of grid cell (PCT_NAT_PFT x PCT_NATVEG / 100)"
    O.createVariable("pct_crop", "f4", ("lat", "lon"), zlib=True)[:] = A.variables["PCT_CROP"][:]
    O.createVariable("landfrac", "f4", ("lat", "lon"), zlib=True)[:] = A.variables["LANDFRAC_PFT"][:]
    O.source = sys.argv[1]
print("wrote", sys.argv[2])
