#!/usr/bin/env python3
"""Compare 1979 downward SW: Chanhyuk JULES forcing (SWdown) vs ours CLM forcing (FSDS).
Both 0.5deg monthly. Annual maps, difference, monthly global mean."""
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

FD = "/Volumes/data01/MOF_LSM_project/data/forcing"
ch = xr.open_dataset(f"{FD}/ch_sw79_mon.nc")
our = xr.open_dataset(f"{FD}/fsds_mon_1979.nc")
lat = ch["lat"].values; lon = ch["lon"].values
sw_ch = ch["SWdown"].values            # (12,360,720)
sw_our = our["FSDS"].values            # (12,360,720), same 0.5deg grid

w = np.cos(np.deg2rad(lat))[:, None]
gm = lambda f: np.array([np.nansum(f[m]*w)/np.nansum(w*np.isfinite(f[m])) for m in range(12)])
gm_ch, gm_our = gm(sw_ch), gm(sw_our)
ann_ch, ann_our = sw_ch.mean(0), sw_our.mean(0)
diff = ann_our - ann_ch

fig = plt.figure(figsize=(14, 9))
def mp(pos, d, title, cmap, vmin, vmax, ext="max"):
    ax = fig.add_subplot(pos, projection=ccrs.PlateCarree())
    im = ax.pcolormesh(lon, lat, d, cmap=cmap, vmin=vmin, vmax=vmax,
                       transform=ccrs.PlateCarree(), shading="auto")
    ax.coastlines(lw=0.4); ax.set_title(title, fontsize=12)
    fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.05, shrink=0.85, extend=ext)
mp(221, ann_ch, "(a) Chanhyuk JULES  SWdown 1979 ann (W/m²)", "inferno", 0, 320)
mp(222, ann_our, "(b) Ours CLM  FSDS 1979 ann (W/m²)", "inferno", 0, 320)
mp(223, diff, "(c) Ours − Chanhyuk (W/m²)", "RdBu_r", -20, 20, ext="both")

ax4 = fig.add_subplot(224)
mon = np.arange(1, 13)
ax4.plot(mon, gm_ch, "-o", color="tab:green", label="Chanhyuk (SWdown)")
ax4.plot(mon, gm_our, "-s", color="tab:red", label="Ours (FSDS)")
ax4.set_xlabel("month"); ax4.set_ylabel("global-mean SW (W/m²)")
ax4.set_xticks(range(1, 13)); ax4.grid(alpha=0.3); ax4.legend()
rmse = np.sqrt(np.nanmean((gm_our - gm_ch)**2))
ax4.set_title(f"monthly global mean  (ann: Chanhyuk={gm_ch.mean():.1f}, Ours={gm_our.mean():.1f}, RMSE={rmse:.2f})")

fig.suptitle("1979 downward shortwave: Chanhyuk (JULES) vs Ours (CLM) ERA5 forcing", fontsize=14, y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.97])
out = "/Volumes/data01/MOF_LSM_project/figures/compare_chanhyuk_ours_sw1979.png"
fig.savefig(out, dpi=140, bbox_inches="tight")
print("saved:", out)
print(f"global-mean ann: Chanhyuk={gm_ch.mean():.2f}  Ours={gm_our.mean():.2f}  RMSE={rmse:.3f}")
print(f"diff(ours-ch) mean={np.nanmean(diff):+.2f}  min={np.nanmin(diff):.1f}  max={np.nanmax(diff):.1f}")
print("Chanhyuk monthly:", np.round(gm_ch, 1))
print("Ours     monthly:", np.round(gm_our, 1))
