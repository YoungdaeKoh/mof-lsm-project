#!/usr/bin/env python3
"""Check map: grassland cover in the observations vs C3 grass in the model, both on the 1-deg grid.

Observation: MODIS MCD12C1 IGBP majority class at 0.05 deg (2010), so each 1-deg cell holds 400 pixels;
  the share of pixels in a class is the class's percent cover at 1 deg (the same quantity as the
  product's Land_Cover_Type_1_Percent layer, aggregated).  Water pixels are excluded.
Model: share of the July 2010 leaf area held by c3grass (base run), from model_species_dominance_1deg_2010.npz.
Top row: grassland / C3-grass share in %.  Bottom row: dominant group where one group holds >= 50 %.
Output: ../figures/check_grass_obs_vs_model_2010.png, ../data/igbp_class_fraction_1deg_2010.npz
"""
import numpy as np
import netCDF4 as nc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature

ig = nc.Dataset("/Volumes/data02/MODIS/MCD12C1/mcd12c1_igbp_GLOBAL_2010_2020.nc")
a = np.asarray(ig["igbp"][0]).reshape(180, 20, 360, 20).transpose(0, 2, 1, 3).reshape(180, 360, 400)
counts = np.apply_along_axis(lambda v: np.bincount(v, minlength=17), 2, a)          # (lat, lon, 17)
land = counts[:, :, 1:].sum(2)
frac = np.where(land[:, :, None] > 0, counts / np.maximum(land, 1)[:, :, None], np.nan)   # share of land pixels
lat = np.arange(-89.5, 90, 1.0); lon = np.arange(-179.5, 180, 1.0)
np.savez("../data/igbp_class_fraction_1deg_2010.npz", lat=lat, lon=lon, fraction=frac.astype("f4"),
         classes="0 Water 1 ENF 2 EBF 3 DNF 4 DBF 5 Mixed 6 ClosedShrub 7 OpenShrub 8 WoodySav 9 Savanna 10 Grass 11 Wetland 12 Crop 13 Urban 14 CropMosaic 15 SnowIce 16 Barren")
obs_grass = frac[:, :, 10] * 100
obs_grass[land < 40] = np.nan                                                           # cells that are < 10 % land

m = np.load("../data/model_species_dominance_1deg_2010.npz", allow_pickle=True)
names = list(m["species"]); share = m["share"]
mod_grass = share[names.index("c3grass")] * 100

# dominant groups (>= 50 %): obs = IGBP groups, model = species
groups = [("Forest", [1, 2, 3, 4, 5]), ("Shrub", [6, 7]), ("Savanna", [8, 9]), ("Grassland", [10]), ("Crop", [12, 14]), ("Barren/snow/wet/urban", [11, 13, 15, 16])]
gcol = ["#1b7837", "#a6611a", "#dfc27d", "#2ca25f", "#e6550d", "#bdbdbd"]
obs_dom = np.full((180, 360), np.nan)
for n, (_, ks) in enumerate(groups):
    f = frac[:, :, ks].sum(2); obs_dom[(f >= 0.5) & ~np.isfinite(obs_dom) & (land >= 40)] = n
obs_dom[(land >= 40) & ~np.isfinite(obs_dom)] = len(groups)
order = ["c3grass", "acer", "picea", "prioria", "c4grass", "larix"]
mcol = ["#2ca25f", "#e6550d", "#08519c", "#756bb1", "#fdd835", "#d62728"]
mod_dom = np.full((180, 360), np.nan)
for n, name in enumerate(order):
    mod_dom[(share[names.index(name)] >= 0.5) & ~np.isfinite(mod_dom)] = n
mod_dom[np.isfinite(share[0]) & ~np.isfinite(mod_dom)] = len(order)

proj = ccrs.PlateCarree()
fig, axs = plt.subplots(2, 2, figsize=(16, 7.4), subplot_kw={"projection": proj}, gridspec_kw={"hspace": 0.25, "wspace": 0.05})
def deco(ax, title):
    ax.coastlines(lw=0.4, color="0.3"); ax.add_feature(cfeature.BORDERS, lw=0.2, edgecolor="0.5")
    ax.set_extent([-180, 180, -60, 85], crs=proj); ax.set_title(title, fontsize=10, loc="left")
    gl = ax.gridlines(draw_labels=True, lw=0.3, color="0.6", ls=":", xlocs=range(-180, 181, 60), ylocs=range(-60, 91, 30))
    gl.top_labels = False; gl.right_labels = False; gl.xlabel_style = {"size": 7}; gl.ylabel_style = {"size": 7}
im = axs[0, 0].pcolormesh(lon, lat, np.ma.masked_invalid(obs_grass), cmap="YlGn", vmin=0, vmax=100, transform=proj, shading="auto")
deco(axs[0, 0], "(a) Observed: IGBP grassland, % of land pixels in the 1° cell (MCD12C1 2010)")
axs[0, 1].pcolormesh(lon, lat, np.ma.masked_invalid(mod_grass), cmap="YlGn", vmin=0, vmax=100, transform=proj, shading="auto")
deco(axs[0, 1], "(b) Model: c3grass, % of the July 2010 leaf area (LM4+ base)")
cb = fig.colorbar(im, ax=axs[0, :].ravel().tolist(), orientation="vertical", pad=0.01, shrink=0.8); cb.set_label("%", fontsize=8)
cm1 = ListedColormap(gcol + ["#f0f0f0"]); nm1 = BoundaryNorm(np.arange(-0.5, len(groups) + 1.5), cm1.N)
im1 = axs[1, 0].pcolormesh(lon, lat, np.ma.masked_invalid(obs_dom), cmap=cm1, norm=nm1, transform=proj, shading="auto")
deco(axs[1, 0], "(c) Observed: IGBP group holding ≥ 50 % of the cell")
cb1 = fig.colorbar(im1, ax=axs[1, 0], orientation="horizontal", pad=0.08, shrink=0.9, ticks=range(len(groups) + 1)); cb1.ax.set_xticklabels([g for g, _ in groups] + ["mixed"], fontsize=7)
cm2 = ListedColormap(mcol + ["#f0f0f0"]); nm2 = BoundaryNorm(np.arange(-0.5, len(order) + 1.5), cm2.N)
im2 = axs[1, 1].pcolormesh(lon, lat, np.ma.masked_invalid(mod_dom), cmap=cm2, norm=nm2, transform=proj, shading="auto")
deco(axs[1, 1], "(d) Model: species holding ≥ 50 % of the July leaf area")
cb2 = fig.colorbar(im2, ax=axs[1, 1], orientation="horizontal", pad=0.08, shrink=0.9, ticks=range(len(order) + 1)); cb2.ax.set_xticklabels(order + ["mixed"], fontsize=7)
fig.savefig("../figures/check_grass_obs_vs_model_2010.png", dpi=150, bbox_inches="tight")
W = np.cos(np.radians(lat))[:, None] * np.ones((1, 360))
for lo, hi in ((50, 70), (20, 50), (-60, 20)):
    b = (lat[:, None] >= lo) & (lat[:, None] < hi) & np.isfinite(obs_grass) & np.isfinite(mod_grass)
    print("%3d-%3dN: obs grassland %4.1f %% of land | model c3grass %4.1f %% of leaf area | cells with obs grass >= 50 %%: %4d, model c3grass >= 50 %%: %4d, both: %4d"
          % (lo, hi, np.nansum(obs_grass[b] * W[b]) / W[b].sum(), np.nansum(mod_grass[b] * W[b]) / W[b].sum(),
             (b & (obs_grass >= 50)).sum(), (b & (mod_grass >= 50)).sum(), (b & (obs_grass >= 50) & (mod_grass >= 50)).sum()))
