#!/usr/bin/env python3
"""Check map: which cells the day-length rules can act on.

Species dominance map of CTRL (base run, July 2010 leaf-area share, 1 deg; same as poster p9) with a grey overlay
where larix + c3grass + acer (the species given a day-length rule) hold >= 50 % of the July leaf area.
input: poster/2026_LM4p_LAI/data/model_species_dominance_1deg_2010.npz (p9)
output: ../figures/c1_species_rule_overlay.png
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm, to_rgb
from matplotlib.patches import Patch
import cartopy.crs as ccrs
import cartopy.feature as cfeature

z = np.load("../../../poster/2026_LM4p_LAI/data/model_species_dominance_1deg_2010.npz", allow_pickle=True)
lat, lon, grid = z["lat"], z["lon"], z["share"]; names = list(z["species"])
order = ["c3grass", "acer", "larix", "picea", "prioria", "c4grass"]          # rule species first
RULE = ("c3grass", "acer", "larix")
pale = lambda c, f=0.5: tuple(f * np.array(to_rgb(c)) + (1 - f))              # blend with white, hue kept
base_col = {"c3grass": "#2ca25f", "acer": "#e6550d", "larix": "#d62728", "picea": "#08519c", "prioria": "#756bb1", "c4grass": "#e6b800"}
colors = [base_col[s] if s in RULE else pale(base_col[s]) for s in order]
dom = np.full((180, 360), np.nan)
for n, name in enumerate(order):
    dom[(grid[names.index(name)] >= 0.5) & ~np.isfinite(dom)] = n
veg = np.isfinite(grid[0]); dom[veg & ~np.isfinite(dom)] = len(order)
rule = sum(np.nan_to_num(grid[names.index(s)]) for s in ("larix", "c3grass", "acer"))
cover = veg & (rule >= 0.5)

W = np.cos(np.radians(lat))[:, None] * np.ones((1, 360))
for a, b in ((-60, 90), (20, 90), (40, 70), (-60, -20)):
    band = veg & (lat[:, None] >= a) & (lat[:, None] < b)
    print("%4d..%3d: rule species >= 50 %% in %5.1f %% of vegetated area (%d cells)" % (a, b, 100 * W[band & cover].sum() / W[band].sum(), (band & cover).sum()))

cmap = ListedColormap(colors + ["#ececec"]); norm = BoundaryNorm(np.arange(-0.5, len(order) + 1.5), cmap.N)
fig = plt.figure(figsize=(12, 5.6)); ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
ax.set_extent([-180, 180, -60, 85], crs=ccrs.PlateCarree(central_longitude=180))
im = ax.pcolormesh(lon, lat, np.ma.masked_invalid(dom), cmap=cmap, norm=norm, transform=ccrs.PlateCarree(), shading="auto")
plt.rcParams["hatch.color"] = "0.15"; plt.rcParams["hatch.linewidth"] = 0.4
ax.contourf(lon, lat, cover.astype(float), levels=[0.5, 1.5], colors="none", hatches=["//////"], transform=ccrs.PlateCarree())
ax.coastlines(lw=0.4, color="0.3"); ax.add_feature(cfeature.BORDERS, lw=0.2, edgecolor="0.5")
gl = ax.gridlines(draw_labels=True, lw=0.3, color="0.6", ls=":", xlocs=range(-180, 181, 60), ylocs=range(-60, 91, 30))
gl.top_labels = False; gl.right_labels = False
cb = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.06, shrink=0.7, ticks=range(len(order) + 1))
cb.ax.set_xticklabels(order + ["mixed"], fontsize=8)
for n, sp_ in enumerate(order):                                              # hatch the rule species in the colour bar too
    if sp_ in RULE:
        cb.ax.add_patch(plt.Rectangle((n - 0.5, 0), 1, 1, fill=False, hatch="//////", lw=0, transform=cb.ax.get_xaxis_transform()))
cb.ax.axvline(2.5, color="k", lw=1.5)
cb.ax.text(1, 1.15, "day-length rule (vivid, hatched)", ha="center", fontsize=8, transform=cb.ax.get_xaxis_transform())
cb.ax.text(4.5, 1.15, "no rule (pale)", ha="center", fontsize=8, transform=cb.ax.get_xaxis_transform())
ax.legend(handles=[Patch(fc="white", ec="0.15", hatch="//////", label="larix + c3grass + acer ≥ 50 % (day-length rule applies)")],
          loc="lower left", fontsize=8, framealpha=0.9)
ax.set_title("CTRL species holding ≥ 50 % of July 2010 leaf area; hatched = cells the day-length rules act on (rule species vivid, others pale)", fontsize=10, loc="left")
fig.savefig("../figures/c1_species_rule_overlay.png", dpi=150, bbox_inches="tight")
