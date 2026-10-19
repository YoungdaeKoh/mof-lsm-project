#!/usr/bin/env python3
"""Why does larix decline after replanting? Track larix vs picea vs acer cohorts through the replant restarts.

Restarts (all Jan-01 03Z): IC 2010 (replanted seed) -> archive y2011..y2015 (= 2012..2016-01-01).
Region: 50-75N, natural/secondary tiles (landuse 3,4, the tiles that were relabelled).
Per species: cohorts, individuals (sum of nindivs over tiles, unweighted by tile area -> totals are relative only),
share of individuals and of crown area in the top layer, nindivs-weighted median height, NSC/bl_max (carbon reserve),
and recruits (cohort_age < 1 yr).
usage: python3 larix_cohort_track.py  -> ../data/replant/larix_cohort_track.txt
"""
import os
import numpy as np
from netCDF4 import Dataset

GRID = "/Volumes/data02/LM4P/postprocess/grid"
RUNS = [("2010-01", "/Volumes/data02/LM4P/cases/replant/IC_y2009_clm5")] + \
       [("%d-01" % (y + 1), "/Volumes/data02/LM4P/cases/replant_2011_2015/archive/y%d" % y) for y in range(2011, 2016)]
SPECIES = ("picea", "larix", "acer")
VARS = ("species", "nindivs", "layer", "hite", "crownarea", "nsc", "bl_max", "cohort_age")

glat = {}
for n in range(1, 7):
    with Dataset(os.path.join(GRID, "C96_grid.tile%d.nc" % n)) as G:
        glat[n] = G.variables["y"][1::2, 1::2]


def load(rdir):
    out = {k: [] for k in VARS}
    for n in range(1, 7):
        with Dataset(os.path.join(rdir, "vegn2.res.tile%d.nc" % n)) as A:
            A.set_auto_mask(False)
            nt, nlat, nlon = len(A.dimensions["tile"]), len(A.dimensions["lat"]), len(A.dimensions["lon"])
            idx = A.variables["cohort_index"][:].astype(np.int64)
            i = idx % nlon; j = (idx // nlon) % nlat; t = (idx // (nlon * nlat)) % nt
            tidx = A.variables["tile_index"][:].astype(np.int64)
            lu = dict(zip(zip(tidx // (nlon * nlat), (tidx // nlon) % nlat, tidx % nlon), A.variables["landuse"][:].astype(int)))
            lu_c = np.array([lu.get(k, -1) for k in zip(t, j, i)])
            keep = (glat[n][j, i] >= 50) & (glat[n][j, i] <= 75) & np.isin(lu_c, (3, 4))
            names = ["".join(ch.decode() if isinstance(ch, bytes) else str(ch) for ch in row).strip("\x00 ").strip()
                     for row in A.variables["species_names"][:]]
            for k in VARS:
                out[k].append(A.variables[k][:][keep])
    return names, {k: np.concatenate(v) for k, v in out.items()}


lines = ["larix vs picea vs acer, replant run, 50-75N natural/secondary tiles (individuals summed over tiles, relative)",
         "%-8s %-6s %8s %10s %7s %7s %7s %7s %7s %8s" % ("date", "sp", "cohorts", "indiv", "top%N", "top%CA", "H50top", "H50und", "nsc/bl", "recruit%")]
for date, rdir in RUNS:
    names, d = load(rdir)
    for s in SPECIES:
        m = d["species"] == names.index(s)
        N = d["nindivs"][m]; top = d["layer"][m] == 1; H = d["hite"][m]; CA = d["crownarea"][m] * N
        def wmed(x, w):
            if w.sum() == 0:
                return np.nan
            o = np.argsort(x); c = np.cumsum(w[o]); return x[o][np.searchsorted(c, 0.5 * c[-1])]
        ratio = np.where(d["bl_max"][m] > 0, d["nsc"][m] / np.maximum(d["bl_max"][m], 1e-12), np.nan)
        lines.append("%-8s %-6s %8d %10.3g %7.1f %7.1f %7.2f %7.2f %7.2f %8.1f" % (
            date, s, m.sum(), N.sum(), 100 * N[top].sum() / max(N.sum(), 1e-30), 100 * CA[top].sum() / max(CA.sum(), 1e-30),
            wmed(H[top], N[top]), wmed(H[~top], N[~top]), np.nanmedian(ratio), 100 * N[d["cohort_age"][m] < 1].sum() / max(N.sum(), 1e-30)))
os.makedirs("../data/replant", exist_ok=True)
open("../data/replant/larix_cohort_track.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
