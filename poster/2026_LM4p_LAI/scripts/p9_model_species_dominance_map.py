#!/usr/bin/env python3
"""Check map: where each LM4+ species holds >= 50 % of the July leaf area (base run 2010).

Input: ../data/base_species_share_july2010_c96.npz (phentest_species_frac_cells.py), binned to 1 deg
(area-weighted mean per box; empty high-latitude boxes filled from the nearest C96 cell).
Output: ../figures/check_model_species_dominance_2010.png, ../data/model_species_dominance_1deg_2010.npz
"""
import numpy as np
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature

lat = np.arange(-89.5, 90, 1.0); lon = np.arange(-179.5, 180, 1.0)
sp = np.load("../data/base_species_share_july2010_c96.npz", allow_pickle=True)
names = list(sp["species"]); share = sp["share"]
good = np.isfinite(share).all(0) & (sp["total_lai"] > 0.05)
ci = np.clip(((sp["lat"] + 90) // 1).astype(int), 0, 179); cj = np.clip(((sp["lon"] + 180) // 1).astype(int), 0, 359)
den = np.zeros((180, 360)); np.add.at(den, (ci[good], cj[good]), sp["area"][good])
grid = np.full((len(names), 180, 360), np.nan)
for k in range(len(names)):
    num = np.zeros((180, 360)); np.add.at(num, (ci[good], cj[good]), share[k][good] * sp["area"][good])
    grid[k] = np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)
# fill 1-deg boxes with land in the model but no C96 centre (narrow boxes at high latitude): nearest cell, only
# within 1.2 deg so oceans stay empty
tree = cKDTree(np.c_[sp["lat"][good], sp["lon"][good]])
gy, gx = np.meshgrid(lat, lon, indexing="ij")
dist, idx = tree.query(np.c_[gy.ravel(), gx.ravel()])
fill = (~np.isfinite(grid[0]).ravel()) & (dist < 1.2)
for k in range(len(names)):
    g = grid[k].ravel(); g[fill] = share[k][good][idx[fill]]; grid[k] = g.reshape(180, 360)
np.savez("../data/model_species_dominance_1deg_2010.npz", lat=lat, lon=lon, species=np.array(names), share=grid.astype("f4"))

order = ["c3grass", "acer", "picea", "prioria", "c4grass", "larix"]
colors = ["#2ca25f", "#e6550d", "#08519c", "#756bb1", "#fdd835", "#d62728"]
dom = np.full((180, 360), np.nan)
for n, name in enumerate(order):
    k = names.index(name); dom[(grid[k] >= 0.5) & ~np.isfinite(dom)] = n
veg = np.isfinite(grid[0]); dom[veg & ~np.isfinite(dom)] = len(order)      # vegetated, no species >= 50 %
cmap = ListedColormap(colors + ["#d9d9d9"]); norm = BoundaryNorm(np.arange(-0.5, len(order) + 1.5), cmap.N)
fig = plt.figure(figsize=(12, 5.6)); ax = plt.axes(projection=ccrs.PlateCarree())
im = ax.pcolormesh(lon, lat, np.ma.masked_invalid(dom), cmap=cmap, norm=norm, transform=ccrs.PlateCarree(), shading="auto")
ax.coastlines(lw=0.4, color="0.3"); ax.add_feature(cfeature.BORDERS, lw=0.2, edgecolor="0.5")
ax.set_extent([-180, 180, -60, 85], crs=ccrs.PlateCarree())
gl = ax.gridlines(draw_labels=True, lw=0.3, color="0.6", ls=":", xlocs=range(-180, 181, 60), ylocs=range(-60, 91, 30))
gl.top_labels = False; gl.right_labels = False
cb = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.06, shrink=0.7, ticks=range(len(order) + 1))
cb.ax.set_xticklabels(order + ["none ≥ 50 %"], fontsize=8)
ax.set_title("LM4+ species holding ≥ 50 % of the July 2010 leaf area (base run), 1°; grey = vegetated but mixed", fontsize=10, loc="left")
fig.savefig("../figures/check_model_species_dominance_2010.png", dpi=150, bbox_inches="tight")
tot = np.isfinite(dom).sum()
print("vegetated 1-deg cells:", tot, "|", " ".join("%s %.1f %%" % (n, 100 * (dom == i).sum() / tot) for i, n in enumerate(order + ["mixed"])))
