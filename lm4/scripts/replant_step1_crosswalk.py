#!/usr/bin/env python3
"""Replanting LM4+ from an observation-based vegetation map, step 1: the crosswalk map.

Input : poster/2026_LM4p_LAI/data/clm5_surfdata_pft_0.9x1.25_simyr2000.nc
        (CLM5 surface dataset, PFT area as % of grid cell; from clm_surfdata_pft_extract.py)
Crosswalk CLM5 PFT -> LM4+ species (decided 2026-10-07, LM4 notes 13.70):
    1 NET temperate, 2 NET boreal           -> picea
    3 NDT boreal                            -> larix
    4 BET tropical, 5 BET temperate (weak)  -> prioria
    6 BDT tropical (weak)                   -> prioria
    7 BDT temperate, 8 BDT boreal           -> acer
    9-11 shrubs (weak)                      -> c3grass
    12 C3 arctic grass, 13 C3 grass         -> c3grass
    14 C4 grass                             -> c4grass
    crop landunit                           -> not a species (land-use tile), kept aside
Output: lm4/data/replant/lm4_species_map_from_clm5.nc  (CLM5 grid, 0.9x1.25)
        tree_frac(species), grass_frac(species) as % of vegetated (non-crop, non-bare) area,
        dom_tree, dom_grass (species index into SPECIES, -1 where that lifeform is absent)
        lm4/data/replant/step1_regional_table.txt and a check map.
"""
import os
import numpy as np
import netCDF4 as nc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature

R = os.path.dirname(os.path.abspath(__file__)) + "/../.."
SRC = R + "/poster/2026_LM4p_LAI/data/clm5_surfdata_pft_0.9x1.25_simyr2000.nc"
OUT = R + "/lm4/data/replant"; os.makedirs(OUT, exist_ok=True)
SPECIES = ["prioria", "picea", "larix", "acer", "c4grass", "c3grass"]   # LM4+ order (field_table / restart species index)
CROSS = {"picea": [1, 2], "larix": [3], "prioria": [4, 5, 6], "acer": [7, 8], "c3grass": [9, 10, 11, 12, 13], "c4grass": [14]}
TREES = ["prioria", "picea", "larix", "acer"]; GRASSES = ["c4grass", "c3grass"]

d = nc.Dataset(SRC)
p = np.asarray(d["pct_pft"][:], "f8"); crop = np.asarray(d["pct_crop"][:], "f8"); lf = np.asarray(d["landfrac"][:], "f8")
lat = np.asarray(d["lat"][:]); lon = np.asarray(d["lon"][:])
veg = p[1:].sum(0)                                     # natural vegetation, % of grid cell (bare and crop excluded)
frac = {s: p[CROSS[s]].sum(0) / np.where(veg > 0, veg, np.nan) * 100 for s in SPECIES}   # % of natural vegetated area
tree_tot = sum(frac[s] for s in TREES); grass_tot = sum(frac[s] for s in GRASSES)
dom_tree = np.full(veg.shape, -1, int); dom_grass = np.full(veg.shape, -1, int)
tstack = np.stack([frac[s] for s in TREES]); gstack = np.stack([frac[s] for s in GRASSES])
has = veg > 0
dom_tree[has & (tree_tot > 0)] = np.argmax(tstack, 0)[has & (tree_tot > 0)]          # index into TREES
dom_grass[has & (grass_tot > 0)] = np.argmax(gstack, 0)[has & (grass_tot > 0)]       # index into GRASSES
dom_tree_sp = np.where(dom_tree >= 0, np.array([SPECIES.index(s) for s in TREES])[np.clip(dom_tree, 0, None)], -1)
dom_grass_sp = np.where(dom_grass >= 0, np.array([SPECIES.index(s) for s in GRASSES])[np.clip(dom_grass, 0, None)], -1)

with nc.Dataset(OUT + "/lm4_species_map_from_clm5.nc", "w") as o:
    o.createDimension("lat", lat.size); o.createDimension("lon", lon.size); o.createDimension("species", len(SPECIES))
    o.createVariable("lat", "f8", ("lat",))[:] = lat; o.createVariable("lon", "f8", ("lon",))[:] = lon
    o.createVariable("species_index", "i4", ("species",))[:] = np.arange(len(SPECIES))
    o.species_names = ", ".join(SPECIES)
    v = o.createVariable("frac", "f4", ("species", "lat", "lon"), zlib=True); v[:] = np.stack([frac[s] for s in SPECIES]); v.long_name = "LM4+ species share of natural vegetated area, %"
    o.createVariable("veg_pct", "f4", ("lat", "lon"), zlib=True)[:] = veg
    o.createVariable("crop_pct", "f4", ("lat", "lon"), zlib=True)[:] = crop
    o.createVariable("landfrac", "f4", ("lat", "lon"), zlib=True)[:] = lf
    a = o.createVariable("dom_tree", "i4", ("lat", "lon")); a[:] = dom_tree_sp; a.long_name = "dominant tree species index (SPECIES order), -1 = no trees"
    b = o.createVariable("dom_grass", "i4", ("lat", "lon")); b[:] = dom_grass_sp; b.long_name = "dominant grass species index (SPECIES order), -1 = no grass"
    o.crosswalk = str(CROSS); o.source = SRC

# checks and regional table
W = np.cos(np.radians(lat))[:, None] * lf * (veg / 100.0)
s = sum(frac[s] for s in SPECIES)
print("fraction sum over species where vegetated: min %.3f max %.3f (should be 100)" % (np.nanmin(s[has]), np.nanmax(s[has])))
lines = ["LM4+ species share of natural vegetated area from the CLM5 map (crosswalk in replant_step1_crosswalk.py), area-weighted %",
         "%-10s " % "band" + " ".join("%8s" % x for x in SPECIES) + "   dominant tree / grass (cells)"]
for lo, hi in ((50, 90), (20, 50), (-60, 20), (-90, 90)):
    m = has & (lat[:, None] >= lo) & (lat[:, None] < hi); w = W * m
    row = " ".join("%8.1f" % (np.nansum(frac[x] * w) / w.sum()) for x in SPECIES)
    dt = " ".join("%s %d" % (t, (m & (dom_tree == i)).sum()) for i, t in enumerate(TREES))
    dg = " ".join("%s %d" % (g, (m & (dom_grass == i)).sum()) for i, g in enumerate(GRASSES))
    lines.append("%3d-%3dN   %s   %s | %s" % (lo, hi, row, dt, dg))
open(OUT + "/step1_regional_table.txt", "w").write("\n".join(lines) + "\n"); print("\n".join(lines))

cols = ["#756bb1", "#08519c", "#d62728", "#e6550d"]
fig, axs = plt.subplots(2, 1, figsize=(10, 8), subplot_kw={"projection": ccrs.PlateCarree()})
for ax, (title, dom, names, cl) in zip(axs, (("(a) dominant tree species (CLM5 map → LM4+)", dom_tree, TREES, cols),
                                         ("(b) dominant grass species", dom_grass, GRASSES, ["#fdd835", "#2ca25f"]))):
    z = np.where(dom >= 0, dom, np.nan); cm = ListedColormap(cl); nm = BoundaryNorm(np.arange(-0.5, len(names) + 0.5), cm.N)
    im = ax.pcolormesh(np.where(lon > 180, lon - 360, lon), lat, np.ma.masked_invalid(z), cmap=cm, norm=nm, transform=ccrs.PlateCarree(), shading="auto")
    ax.coastlines(lw=0.4, color="0.3"); ax.add_feature(cfeature.BORDERS, lw=0.2, edgecolor="0.5"); ax.set_extent([-180, 180, -60, 85])
    ax.set_title(title, fontsize=10, loc="left")
    gl = ax.gridlines(draw_labels=True, lw=0.3, color="0.6", ls=":", xlocs=range(-180, 181, 60), ylocs=range(-60, 91, 30)); gl.top_labels = False; gl.right_labels = False
    cb = fig.colorbar(im, ax=ax, orientation="vertical", pad=0.02, shrink=0.8, ticks=range(len(names))); cb.ax.set_yticklabels(names, fontsize=8)
fig.savefig(OUT + "/check_step1_dominant_species.png", dpi=130, bbox_inches="tight")
