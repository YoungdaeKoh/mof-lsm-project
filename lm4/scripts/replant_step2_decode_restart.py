#!/usr/bin/env python3
"""Replanting step 2: decode the vegetation restart so every cohort has a tile, a cell and coordinates.

vegn2.res.tileN.nc stores cohorts along one compressed axis, cohort_index, with
compress = "cohort tile lat lon": index = ((c * ntile + t) * nlat + j) * nlon + i.
Cell centres come from the C96 supergrid (odd rows/cols), as in lm4p_to_latlon.py.
Check: the set of cells holding larix cohorts must match the 20 cells with larix leaf area in the
July output (phentest_species_frac_cells.py), and the species census must equal restart_species_census.py.
usage: python replant_step2_decode_restart.py <restart_dir> <out.npz>
"""
import glob
import os
import sys
import numpy as np
from netCDF4 import Dataset

GRID = "/Volumes/data02/LM4P/postprocess/grid"
rdir, out = sys.argv[1], sys.argv[2]
NX = 96
rec = []
for n in range(1, 7):
    f = os.path.join(rdir, "vegn2.res.tile%d.nc" % n)
    with Dataset(os.path.join(GRID, "C96_grid.tile%d.nc" % n)) as G:
        glat = G.variables["y"][1::2, 1::2]; glon = G.variables["x"][1::2, 1::2]
    with Dataset(f) as A:
        A.set_auto_mask(False)
        nt, nlat, nlon = len(A.dimensions["tile"]), len(A.dimensions["lat"]), len(A.dimensions["lon"])
        idx = A.variables["cohort_index"][:].astype(np.int64)
        i = idx % nlon; j = (idx // nlon) % nlat; t = (idx // (nlon * nlat)) % nt; c = idx // (nlon * nlat * nt)
        tidx = A.variables["tile_index"][:].astype(np.int64)
        ti = tidx % nlon; tj = (tidx // nlon) % nlat; tt = tidx // (nlon * nlat)
        lu_tile = A.variables["landuse"][:].astype(int)
        lu = dict(zip(map(tuple, np.c_[tt, tj, ti]), lu_tile))
        lu_c = np.array([lu.get((a, b, d), -1) for a, b, d in zip(t, j, i)])
        names = ["".join(ch.decode() if isinstance(ch, bytes) else str(ch) for ch in row).strip("\x00 ").strip() for row in A.variables["species_names"][:]]
        rec.append(dict(face=np.full(idx.size, n), c=c, t=t, j=j, i=i, lat=glat[j, i], lon=np.where(glon[j, i] > 180, glon[j, i] - 360, glon[j, i]),
                        landuse=lu_c, species=A.variables["species"][:], nindivs=A.variables["nindivs"][:], bl=A.variables["bl"][:],
                        crownarea=A.variables["crownarea"][:], dbh=A.variables["dbh"][:]))
R = {k: np.concatenate([r[k] for r in rec]) for k in rec[0]}
np.savez(out, species_names=np.array(names), **R)
print("cohorts", R["species"].size, "| species:", names)
print("landuse codes on cohorts:", dict(zip(*np.unique(R["landuse"], return_counts=True))))
for k, nm in enumerate(names):
    m = R["species"] == k
    if m.sum():
        cells = set(zip(R["face"][m], R["j"][m], R["i"][m]))
        print("  %-8s cohorts %7d in %6d cells | lat range %6.1f..%6.1f" % (nm, m.sum(), len(cells), R["lat"][m].min(), R["lat"][m].max()))
