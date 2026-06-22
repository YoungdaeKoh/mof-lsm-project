#!/usr/bin/env python3
"""
Compare our ERA5 forcing shortwave (FSDS) vs GSWP3 Solar, 1979 annual mean.
Both on the same 0.5deg GSWP3 grid (360x720). Difference = ERA5 - GSWP3.
Panels: (a) ERA5 map, (b) GSWP3 map, (c) diff map, (d) diff histogram + zonal diff.
"""
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib import gridspec
try:
    import cartopy.crs as ccrs
    from cartopy.util import add_cyclic_point
    HAS = True
except Exception:
    HAS = False

ERA5 = "/Volumes/data01/MOF_LSM_project/data/forcing/era5_1979_annmean.nc"
GSWP = "/Volumes/data01/MOF_LSM_project/data/gswp3_solr_1979_annmean.nc"
FIG  = "/Volumes/data01/MOF_LSM_project/figures/compare_fsds_gswp3.png"

de = xr.open_dataset(ERA5)
dg = xr.open_dataset(GSWP)
lat = de["LATIXY"].values[:, 0]
lon = de["LONGXY"].values[0, :]
era = de["FSDS"].mean("time").values          # annual mean (360,720)
gsw = dg["FSDS"].values                        # (360,720)
if gsw.ndim == 3: gsw = gsw[0]
diff = era - gsw

# stats
print(f"ERA5  mean={np.nanmean(era):.2f}  GSWP3 mean={np.nanmean(gsw):.2f}  W/m2")
print(f"diff  mean={np.nanmean(diff):+.2f}  std={np.nanstd(diff):.2f}  "
      f"min={np.nanmin(diff):+.1f}  max={np.nanmax(diff):+.1f}")
for p in [5, 25, 50, 75, 95]:
    print(f"  p{p:02d} = {np.nanpercentile(diff, p):+.2f}")
print(f"|diff|<10 W/m2 : {100*np.mean(np.abs(diff)<10):.1f}% of grid")

fig = plt.figure(figsize=(14, 9))
gs = gridspec.GridSpec(2, 2, hspace=0.25, wspace=0.12)
def mp(pos, data, title, cmap, vmin, vmax, ext):
    d, lo = (add_cyclic_point(data, coord=lon) if HAS else (data, lon))
    ax = fig.add_subplot(pos, projection=ccrs.PlateCarree()) if HAS else fig.add_subplot(pos)
    kw = dict(transform=ccrs.PlateCarree()) if HAS else {}
    im = ax.pcolormesh(lo, lat, d, cmap=cmap, vmin=vmin, vmax=vmax, shading="auto", **kw)
    if HAS: ax.coastlines(lw=0.4); ax.set_global()
    ax.set_title(title, fontsize=13)
    fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.04, shrink=0.85, extend=ext)
    return ax
mp(gs[0,0], era,  "(a) ERA5 forcing FSDS (1979)",  "inferno", 0, 320, "max")
mp(gs[0,1], gsw,  "(b) GSWP3 Solar FSDS (1979)",   "inferno", 0, 320, "max")
mp(gs[1,0], diff, "(c) difference  ERA5 - GSWP3",  "RdBu_r", -40, 40, "both")

# (d) histogram + zonal mean diff
axd = fig.add_subplot(gs[1,1])
axd.hist(diff.ravel(), bins=120, range=(-60, 60), color="tab:gray", alpha=0.8)
axd.axvline(0, color="k", lw=0.8)
axd.axvline(np.nanmean(diff), color="red", lw=1.5, ls="--",
            label=f"mean {np.nanmean(diff):+.1f}")
axd.set_xlabel("FSDS difference  ERA5 - GSWP3 (W/m²)", fontsize=12)
axd.set_ylabel("grid count", fontsize=12); axd.legend(fontsize=11)
axd.set_title("(d) difference distribution", fontsize=13)
# inset: zonal-mean diff
axz = axd.inset_axes([0.62, 0.55, 0.36, 0.4])
axz.plot(np.nanmean(diff, axis=1), lat, color="tab:blue", lw=1.3)
axz.axvline(0, color="k", lw=0.6); axz.set_title("zonal-mean (W/m²)", fontsize=8)
axz.tick_params(labelsize=7); axz.set_ylabel("lat", fontsize=7)

fig.suptitle("Shortwave forcing comparison: ERA5 (ours) vs GSWP3 — 1979 annual mean, 0.5° grid", fontsize=14)
fig.savefig(FIG, dpi=140, bbox_inches="tight")
print("saved:", FIG)
