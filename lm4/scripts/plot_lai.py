#!/opt/homebrew/bin/python3
# Prescribed LAI map: bin cubed-sphere land points onto a regular 1deg grid
# (removes cubed-sphere scatter fan artifacts), then pcolormesh.
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

d = np.load("/tmp/lai_map_data.npz")
lon, lat, lai = d["lon"], d["lat"], d["lai"]
lon = np.where(lon > 180, lon - 360, lon)

# bin onto regular 1deg grid: mean LAI per cell
res = 2.0
lon_e = np.arange(-180, 180 + res, res)
lat_e = np.arange(-90, 90 + res, res)
ssum, _, _ = np.histogram2d(lon, lat, bins=[lon_e, lat_e], weights=lai)
cnt, _, _ = np.histogram2d(lon, lat, bins=[lon_e, lat_e])
grid = np.where(cnt > 0, ssum / np.maximum(cnt, 1), np.nan)
grid = np.ma.masked_invalid(grid.T)            # (lat, lon)

fig = plt.figure(figsize=(12, 5.6))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_global()
ax.add_feature(cfeature.COASTLINE, lw=0.4, edgecolor="0.3")
lon_c = 0.5 * (lon_e[:-1] + lon_e[1:]); lat_c = 0.5 * (lat_e[:-1] + lat_e[1:])
pm = ax.pcolormesh(lon_e, lat_e, grid, cmap="YlGn", vmin=0, vmax=7,
                   transform=ccrs.PlateCarree(), shading="flat")
cb = plt.colorbar(pm, ax=ax, orientation="vertical", shrink=0.78, pad=0.02, extend="max")
cb.set_label("LAI (m$^2$ m$^{-2}$)")
ax.set_title(f"LM4 prescribed LAI (static veg, annual, regridded 1°)  —  land-mean = {lai.mean():.2f}",
             fontsize=12, fontweight="bold")
gl = ax.gridlines(draw_labels=True, lw=0.3, color="0.7", alpha=0.5)
gl.top_labels = False; gl.right_labels = False
out = "/Volumes/data01/MOF_LSM_project/figures/lm4_lai_map.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
print("saved:", out)
