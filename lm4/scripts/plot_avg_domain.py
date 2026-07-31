"""Which cells the LM4+ global land mean is actually taken over.

The time-series figures average over C96 land points, but not all of them:
variables carried on soil_area already drop Antarctica, and Greenland is removed
by its Natural Earth outline (greenland_mask.py).  Drawn on a 2-degree display
grid so the domain reads as coverage rather than as scattered C96 dots.

A 2-degree box counts as used if it holds at least one averaged point; boxes
that hold land but no averaged point are the excluded ones.

Input : lm4/data/lm4_lai_1982_1996.npz  (lat, lon, keep, ann_1990)
Output: figures/lm4_avg_domain.png
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature

z = np.load("lm4/data/lm4_lai_1982_1996.npz")
lat = z["lat"]
lon = np.where(z["lon"] > 180, z["lon"] - 360, z["lon"])
keep = z["keep"]                      # False inside the Greenland outline
soil = np.isfinite(z["ann_1990"])     # soil_area > 0, i.e. not ice sheet

used = soil & keep
excluded = ~used

w = np.cos(np.deg2rad(lat))
print("C96 land points          %6d" % lat.size)
print("  ice sheet (no soil)    %6d" % (~soil).sum())
print("  Greenland outline cut  %6d" % (soil & ~keep).sum())
print("  USED in the land mean  %6d  (%.1f %% of land area)"
      % (used.sum(), 100 * w[used].sum() / w.sum()))

DL = 2.0
NLAT, NLON = int(180 / DL), int(360 / DL)
blat = 90 - DL / 2 - np.arange(NLAT) * DL
blon = -180 + DL / 2 + np.arange(NLON) * DL
bi = np.clip(((90.0 - lat) / DL).astype(int), 0, NLAT - 1)
bj = np.clip(((lon + 180.0) / DL).astype(int), 0, NLON - 1)

grid = np.zeros((NLAT, NLON))                      # 0 = ocean / no land
np.add.at(grid, (bi[excluded], bj[excluded]), 0)   # keep the array shape honest
has_land = np.zeros((NLAT, NLON), bool)
has_used = np.zeros((NLAT, NLON), bool)
np.logical_or.at(has_land, (bi, bj), True)
np.logical_or.at(has_used, (bi[used], bj[used]), True)

field = np.full((NLAT, NLON), np.nan)
field[has_land] = 0.0                              # land but nothing averaged
field[has_used] = 1.0                              # at least one averaged point
print("  2-deg boxes: used %d, excluded-only %d"
      % (has_used.sum(), (has_land & ~has_used).sum()))

cmap = ListedColormap(["#b8d4e8", "#2c7a3f"])      # excluded, used
norm = BoundaryNorm([-0.5, 0.5, 1.5], cmap.N)

proj = ccrs.PlateCarree()
fig = plt.figure(figsize=(14, 7))
ax = fig.add_subplot(1, 1, 1, projection=proj)
ax.set_extent([-180, 180, -90, 90], crs=proj)
ax.pcolormesh(blon, blat, np.ma.masked_invalid(field), cmap=cmap, norm=norm,
              transform=proj, shading="nearest")
ax.add_feature(cfeature.COASTLINE, lw=0.5)
gl = ax.gridlines(draw_labels=True, lw=0.3, alpha=0.4)
gl.top_labels = False
gl.right_labels = False
gl.xlabel_style = {"size": 11}
gl.ylabel_style = {"size": 11}
handles = [plt.Rectangle((0, 0), 1, 1, fc="#2c7a3f", ec="none"),
           plt.Rectangle((0, 0), 1, 1, fc="#b8d4e8", ec="none")]
ax.legend(handles,
          ["averaged  (%d C96 points, %.0f %% of land area)"
           % (used.sum(), 100 * w[used].sum() / w.sum()),
           "excluded: ice sheet + Greenland  (%d points)" % excluded.sum()],
          loc="lower left", fontsize=11, framealpha=0.93)
ax.set_title("Averaging domain of the LM4+ global land mean\n"
             "C96 land points with soil_area > 0, Greenland removed by its "
             "outline;  shown on a 2° grid", fontsize=14)
fig.tight_layout()
fig.savefig("figures/lm4_avg_domain.png", dpi=150)
print("\nwrote figures/lm4_avg_domain.png")
