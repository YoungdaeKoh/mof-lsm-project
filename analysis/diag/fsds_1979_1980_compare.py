#!/usr/bin/env python3
"""Compare ERA5 input FSDS: 1979 vs 1980 (annual maps, difference, monthly global mean)."""
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

FD = "/Volumes/data01/MOF_LSM_project/data/forcing"
g = xr.open_dataset(f"{FD}/era5_1979_annmean.nc")
ilat = g["LATIXY"].values[:, 0]
ilon = g["LONGXY"].values[0, :]

def load(y):
    return xr.open_dataset(f"{FD}/fsds_mon_{y}.nc")["FSDS"].values  # (12,360,720)

f79, f80 = load(1979), load(1980)
w = np.cos(np.deg2rad(ilat))[:, None]
gmean = lambda f: np.array([np.nansum(f[m] * w) / np.nansum(w * np.isfinite(f[m]))
                            for m in range(12)])
gm79, gm80 = gmean(f79), gmean(f80)
ann79, ann80 = f79.mean(0), f80.mean(0)

fig = plt.figure(figsize=(14, 9))
def mp(pos, d, title, cmap, vmin, vmax):
    ax = fig.add_subplot(pos, projection=ccrs.PlateCarree())
    im = ax.pcolormesh(ilon, ilat, d, cmap=cmap, vmin=vmin, vmax=vmax,
                       transform=ccrs.PlateCarree(), shading="auto")
    ax.coastlines(lw=0.4); ax.set_title(title, fontsize=12)
    fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.05, shrink=0.8)
    return ax

mp(221, ann79, "1979 annual FSDS (W/m²)", "inferno", 0, 320)
mp(222, ann80, "1980 annual FSDS (W/m²)", "inferno", 0, 320)
mp(223, ann80 - ann79, "1980 − 1979 (W/m²)", "RdBu_r", -30, 30)

ax4 = fig.add_subplot(224)
mon = np.arange(1, 13)
ax4.plot(mon, gm79, "-o", color="tab:blue", label="1979")
ax4.plot(mon, gm80, "-s", color="tab:red", label="1980")
ax4.set_xlabel("month"); ax4.set_ylabel("global-mean FSDS (W/m²)")
ax4.set_xticks(range(1, 13)); ax4.grid(alpha=0.3); ax4.legend()
ax4.set_title(f"monthly global mean  (1979={gm79.mean():.1f}, 1980={gm80.mean():.1f})")

fig.suptitle("ERA5 input FSDS: 1979 vs 1980", fontsize=14, y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.97])
out = "/Volumes/data01/MOF_LSM_project/figures/fsds_1979_1980_compare.png"
fig.savefig(out, dpi=140, bbox_inches="tight")
print("saved:", out)
print(f"global-mean diff (1980-1979): {(gm80.mean()-gm79.mean()):+.2f} W/m²")
print(f"1979 monthly: {np.round(gm79,1)}")
print(f"1980 monthly: {np.round(gm80,1)}")
