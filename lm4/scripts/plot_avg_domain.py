"""Which cells the LM4+ global land mean is actually taken over.

The time-series figures average over C96 land points, but not all of them:
variables carried on soil_area already drop Antarctica, and a Greenland box is
cut by hand (Iceland kept).  This draws the three groups so the averaging domain
is on record next to the numbers.

Input : lm4/data/lm4_lai_1982_1996.npz  (lat, lon, keep, ann_1990)
Output: figures/lm4_avg_domain.png
"""
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

z = np.load("lm4/data/lm4_lai_1982_1996.npz")
lat = z["lat"]
lon = np.where(z["lon"] > 180, z["lon"] - 360, z["lon"])
keep = z["keep"]                      # False inside the Greenland box
soil = np.isfinite(z["ann_1990"])     # soil_area > 0, i.e. not ice sheet

used = soil & keep
ice = ~soil
grn = soil & ~keep

print("C96 land points          %6d" % lat.size)
print("  ice sheet (no soil)    %6d   lat %.1f .. %.1f" % (ice.sum(), lat[ice].min(), lat[ice].max()))
print("  Greenland box cut      %6d" % grn.sum())
print("  USED in the land mean  %6d" % used.sum())
w = np.cos(np.deg2rad(lat))
print("  used share of land area  %.1f %%" % (100 * w[used].sum() / w.sum()))

proj = ccrs.PlateCarree()
fig = plt.figure(figsize=(13, 6.4))
ax = fig.add_subplot(1, 1, 1, projection=proj)
ax.set_extent([-180, 180, -90, 90], crs=proj)
ax.add_feature(cfeature.COASTLINE, lw=0.45)
ax.scatter(lon[used], lat[used], s=1.4, marker="s", c="#2c7a3f",
           transform=proj, linewidths=0,
           label="used in the land mean  (n=%d)" % used.sum())
ax.scatter(lon[ice], lat[ice], s=1.4, marker="s", c="#7fb3d5",
           transform=proj, linewidths=0,
           label="ice sheet, no soil tile  (n=%d)" % ice.sum())
ax.scatter(lon[grn], lat[grn], s=5.0, marker="s", c="#e07b39",
           transform=proj, linewidths=0,
           label="Greenland box cut by hand  (n=%d)" % grn.sum())
gl = ax.gridlines(draw_labels=True, lw=0.3, alpha=0.4)
gl.top_labels = False
gl.right_labels = False
gl.xlabel_style = {"size": 8}
gl.ylabel_style = {"size": 8}
ax.legend(loc="lower left", fontsize=9, markerscale=6, framealpha=0.92)
ax.set_title("Averaging domain of the LM4+ global land mean — C96 land points\n"
             "soil_area > 0 minus a Greenland box (Iceland kept); "
             "Antarctica has no soil tile at all", fontsize=11)
fig.tight_layout()
fig.savefig("figures/lm4_avg_domain.png", dpi=150)
print("\nwrote figures/lm4_avg_domain.png")
