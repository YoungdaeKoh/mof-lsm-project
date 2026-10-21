#!/usr/bin/env python3
"""How is vegetation organised in LM4p (PPA)? Tiles per grid cell, cohorts per tile, canopy layers, from the
daylhold5_d vegetation restart (end of 2010 = 1 Jan 2011, C96, 6 faces).

Restart compression (verified: tile k 0..17, cohort c 0..63, 3838 cells on face 1 = land_month grid_index count):
  tile_index   = k*NY*NX + j*NX + i
  cohort_index = c*NT*NY*NX + k*NY*NX + j*NX + i
Codes (vegn_data.F90:71-99): status 0 = LEAF_ON, 5 = LEAF_OFF; landuse 1 pasture, 2 crop, 3 natural, 4 secondary.
Latitude per cell from land_daily geolat_t on grid_index (flat j*NX+i). Counts are unweighted (tile area fractions are
not in the vegetation restart). Winter state: deciduous leaves mostly off.
output: ../data/cohort_structure_y2011jan.txt
"""
import numpy as np
from netCDF4 import Dataset

RS = "/Volumes/data02/LM4P/cases/phentest_2010/daylhold5_d/RESTART_vegn/vegn2.res.tile%d.nc"
LD = "/Volumes/data02/LM4P/cases/phentest_2010/daylhold5_d/20100101.land_daily.tile%d.nc"
SP = ["prioria", "picea", "larix", "acer", "c4grass", "c3grass", "default"]
LU = {1: "pasture", 2: "crop", 3: "natural", 4: "secondary"}
NX = NY = 96

tiles, cohorts = [], []          # tiles: (face, cell, k, lat, landuse, age); cohorts: per-cohort records
for f in range(1, 7):
    with Dataset(LD % f) as A:
        A.set_auto_mask(False)
        gi = A["grid_index"][:].astype(int).ravel(); gl = A["geolat_t"][:].ravel()
    latof = dict(zip(gi, gl))
    with Dataset(RS % f) as A:
        A.set_auto_mask(False)
        NT = A.dimensions["tile"].size
        ti = A["tile_index"][:].astype(np.int64); ci = A["cohort_index"][:].astype(np.int64)
        lu = A["landuse"][:]; age = A["age_since_disturbance"][:]
        cell_t = ti % (NX * NY); k_t = ti // (NX * NY)
        assert set(np.unique(cell_t)) <= set(latof), "restart cell not in grid_index"
        for n in range(ti.size):
            tiles.append((f, cell_t[n], k_t[n], latof[cell_t[n]], lu[n], age[n]))
        r = ci % (NT * NX * NY)
        v = {x: A[x][:] for x in ("species", "hite", "layer", "nindivs", "status", "crownarea", "bl", "gdd")}
        for n in range(ci.size):
            cohorts.append((f, r[n] % (NX * NY), r[n] // (NX * NY), v["species"][n], v["hite"][n], v["layer"][n],
                            v["nindivs"][n], v["status"][n], v["crownarea"][n], v["bl"][n], v["gdd"][n]))

T = np.array(tiles, dtype=[("f", "i4"), ("cell", "i8"), ("k", "i4"), ("lat", "f8"), ("lu", "i4"), ("age", "f8")])
C = np.array(cohorts, dtype=[("f", "i4"), ("cell", "i8"), ("k", "i4"), ("sp", "i4"), ("h", "f8"), ("layer", "i4"),
                             ("n", "f8"), ("st", "i4"), ("ca", "f8"), ("bl", "f8"), ("gdd", "f8")])
tkey = T["f"] * 10**8 + T["cell"] * 100 + T["k"]
ckey = C["f"] * 10**8 + C["cell"] * 100 + C["k"]
ncoh = dict(zip(*np.unique(ckey, return_counts=True)))
T_ncoh = np.array([ncoh.get(x, 0) for x in tkey])
nlay = {}
for x, l in zip(ckey, C["layer"]):
    nlay[x] = max(nlay.get(x, 0), l)
T_nlay = np.array([nlay.get(x, 0) for x in tkey])
cellkey = T["f"] * 10**6 + T["cell"]
ucell, ntile = np.unique(cellkey, return_counts=True)
cell_lat = dict(zip(cellkey, T["lat"]))

L = ["LM4p vegetation structure, daylhold5_d restart 1 Jan 2011 (C96), unweighted counts",
     "totals: cells %d, vegetated tiles %d, cohorts %d" % (ucell.size, T.size, C.size)]
L.append("\nTiles per grid cell by latitude band: mean / median / max")
for lo, hi in [(-60, -20), (-20, 20), (20, 40), (40, 50), (50, 70), (70, 90)]:
    m = np.array([lo <= cell_lat[c] < hi for c in ucell])
    if m.any():
        L.append("  %4d..%3dN cells %5d | %.1f / %.0f / %d" % (lo, hi, m.sum(), ntile[m].mean(), np.median(ntile[m]), ntile[m].max()))
L.append("\nTiles by land use: count, cohorts per tile mean/median/max, canopy layers mean/max, age since disturbance median (yr)")
for code, name in LU.items():
    m = T["lu"] == code
    if m.any():
        L.append("  %-9s %6d | %.1f / %.0f / %d | %.2f / %d | %.0f" % (name, m.sum(), T_ncoh[m].mean(), np.median(T_ncoh[m]),
                 T_ncoh[m].max(), T_nlay[m].mean(), T_nlay[m].max(), np.median(T["age"][m])))
L.append("\nCohorts per tile, 50-70N natural tiles, by species (tiles where present): presence %, mean / max cohorts, height median (m)")
tm = (T["lu"] == 3) & (T["lat"] >= 50) & (T["lat"] < 70)
tset = set(tkey[tm])
inb = np.array([x in tset for x in ckey])
for s, name in enumerate(SP):
    ms = inb & (C["sp"] == s)
    if not ms.any():
        continue
    keys, cnt = np.unique(ckey[ms], return_counts=True)
    L.append("  %-8s %5.1f%% | %.1f / %d | %.1f" % (name, 100 * keys.size / len(tset), cnt.mean(), cnt.max(), np.median(C["h"][ms])))

# example: the 50-70N natural tile with the most cohorts among tiles holding picea, acer and c3grass
cand = {}
for x, s in zip(ckey[inb], C["sp"][inb]):
    cand.setdefault(x, set()).add(s)
ok = [x for x, s in cand.items() if {1, 3, 5} <= s]
if ok:
    best = max(ok, key=lambda x: ncoh[x])
    mt = tkey == best
    L.append("\nExample tile (50-70N natural, has picea+acer+c3grass, most cohorts): face %d cell %d tile %d lat %.1f, "
             "age %.0f yr, %d cohorts, tiles in this cell %d" % (T["f"][mt][0], T["cell"][mt][0], T["k"][mt][0],
             T["lat"][mt][0], T["age"][mt][0], ncoh[best], ntile[ucell == cellkey[mt][0]][0]))
    L.append("  %-8s %6s %5s %10s %9s %7s %6s" % ("species", "height", "layer", "n per m2", "crown m2", "status", "GDD"))
    mc = np.where(ckey == best)[0]
    for n in mc[np.argsort(-C["h"][mc])]:
        L.append("  %-8s %6.1f %5d %10.4f %9.2f %7s %6.0f" % (SP[C["sp"][n]], C["h"][n], C["layer"][n], C["n"][n],
                 C["ca"][n], "ON" if C["st"][n] == 0 else "OFF", C["gdd"][n]))

open("../data/cohort_structure_y2011jan.txt", "w").write("\n".join(L) + "\n")
print("\n".join(L))
