#!/usr/bin/env python3
"""Fig. 1 inset / panel: the seven boreal AR6 land regions used in the paper.

Regions = IPCC AR6 land reference regions (Iturbide et al. 2020, ESSD 12, 2959), polygons from
regionmask.defined_regions.ar6.land. Filled = the four regions shown as seasonal cycles in Fig. 1a-d,
outlined = the other three in the bias bars (Fig. 1e). Background: GIMMS LAI4g 2001-2015 annual mean.
output: ../figures/f1b_region_map.png
"""
import warnings
import numpy as np
import netCDF4 as nc
import regionmask
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

P = "../../../poster/2026_LM4p_LAI/data/"
with nc.Dataset(P + "gimms_lai_mon_1982_2020.nc") as d:
    name = [v for v in d.variables if d.variables[v].ndim == 3][0]
    lai = np.ma.filled(d[name][(2001 - 1982) * 12:(2016 - 1982) * 12].astype("f8"), np.nan)
    lat = np.asarray(d["lat"][:]); lon = np.asarray(d["lon"][:])
lai[np.abs(lai) > 100] = np.nan
ann = np.nanmean(lai, 0)

ar6 = regionmask.defined_regions.ar6.land
CYC = ["NEU", "RFE", "NWN", "ESB"]           # Fig. 1a-d
BAR = ["WSB", "NEN", "RAR"]                  # bars only
COL = {"NEU": "#1b9e77", "RFE": "#d95f02", "NWN": "#7570b3", "ESB": "#e7298a"}

fig = plt.figure(figsize=(12, 3.4))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree(central_longitude=10))
ax.set_extent([-170, 180, 38, 82], crs=ccrs.PlateCarree())
im = ax.pcolormesh(lon, lat, np.ma.masked_invalid(ann), cmap="Greens", vmin=0, vmax=4, transform=ccrs.PlateCarree(), shading="auto")
ax.coastlines(lw=0.4, color="0.3"); ax.add_feature(cfeature.OCEAN, facecolor="#eef3f7", zorder=0)
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    for ab in CYC + BAR:
        r = ar6[ab]
        geoms = [r.polygon] if r.polygon.geom_type == "Polygon" else list(r.polygon.geoms)
        for g in geoms:
            x, y = g.exterior.xy
            if ab in CYC:
                ax.fill(x, y, color=COL[ab], alpha=0.28, transform=ccrs.PlateCarree(), lw=0)
                ax.plot(x, y, color=COL[ab], lw=2.0, transform=ccrs.PlateCarree())
            else:
                ax.plot(x, y, color="0.15", lw=1.6, ls="--", transform=ccrs.PlateCarree())
        cx, cy = r.centroid
        if ab == "RAR":
            cy = 70
        ax.text(cx, cy, ab, transform=ccrs.PlateCarree(), ha="center", va="center", fontsize=11, weight="bold",
                color="k", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8))
gl = ax.gridlines(draw_labels=True, lw=0.3, color="0.6", ls=":", xlocs=range(-180, 181, 60), ylocs=range(40, 81, 20))
gl.top_labels = False; gl.right_labels = False; gl.xlabel_style = {"size": 8}; gl.ylabel_style = {"size": 8}
ax.set_aspect("auto")
cb = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.12, shrink=0.45, aspect=35); cb.set_label("GIMMS LAI4g annual mean 2001–2015 (m$^2$ m$^{-2}$)", fontsize=8)
ax.set_title("IPCC AR6 land regions used: filled = seasonal cycles (Fig. 1a–d), dashed = bias bars only (Fig. 1e)", loc="left", fontsize=10)
fig.savefig("../figures/f1b_region_map.png", dpi=200, bbox_inches="tight")
print("ok")
