"""LM4 vs GIMMS LAI4g, JJA 1982: side-by-side + difference.

LM4 is on C96 land points (scatter); GIMMS is 0.5deg regular (pcolormesh).
For the difference, GIMMS is sampled at each LM4 point (nearest 0.5deg cell),
so the difference lives on the LM4 points where GIMMS has valid (vegetated) data.
"""
import numpy as np
import netCDF4 as nc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# --- LM4 ---
z = np.load("lm4_lai_jja1982.npz")
plat, plon, plai = z["lat"], z["lon"], z["lai"]

# --- GIMMS JJA 1982 (time idx 5,6,7) ---
d = nc.Dataset("/Volumes/data02/LAI/GIMMS_LAI4g_V1.2_1982_2020.nc")
glat = d.variables["latitude"][:]         # -90..90 asc, 0.5
glon = d.variables["longitude"][:]        # 0..359.5
G = np.stack([np.ma.filled(d.variables["lai"][i].astype("f8"), np.nan)
              for i in (5, 6, 7)])
G[G > 100] = np.nan                        # mask fill 65535
gjja = np.nanmean(G, axis=0)               # (361, 720)
d.close()

# --- sample GIMMS at LM4 points (nearest cell) ---
lon360 = np.where(plon < 0, plon + 360, plon)
ilat = np.clip(np.round((plat - glat[0]) / 0.5).astype(int), 0, len(glat) - 1)
ilon = (np.round((lon360 - glon[0]) / 0.5).astype(int)) % len(glon)
gsamp = gjja[ilat, ilon]
diff = plai - gsamp                         # LM4 - GIMMS, NaN where GIMMS masked

both = np.isfinite(diff)
print("co-located points: %d" % both.sum())
print("LM4  mean over those: %.3f" % np.nanmean(plai[both]))
print("GIMMS mean over those: %.3f" % np.nanmean(gsamp[both]))
print("bias (LM4-GIMMS): %.3f  RMSD: %.3f" % (
    np.nanmean(diff[both]), np.sqrt(np.nanmean(diff[both] ** 2))))
r = np.corrcoef(plai[both], gsamp[both])[0, 1]
print("spatial corr: %.3f" % r)

# --- plot ---
fig, axes = plt.subplots(1, 3, figsize=(22, 5.2),
                         subplot_kw={"projection": ccrs.PlateCarree()})

s1 = axes[0].scatter(plon, plat, c=plai, s=3, cmap="YlGn", vmin=0, vmax=6,
                     transform=ccrs.PlateCarree())
axes[0].set_title("LM4 offline LAI, JJA 1982 (C96)", fontsize=12)
fig.colorbar(s1, ax=axes[0], orientation="horizontal", shrink=0.85, pad=0.03, label="LAI")

lon2d, lat2d = np.meshgrid(glon, glat)
s2 = axes[1].pcolormesh(lon2d, lat2d, gjja, cmap="YlGn", vmin=0, vmax=6,
                        transform=ccrs.PlateCarree(), shading="auto")
axes[1].set_title("GIMMS LAI4g, JJA 1982 (0.5°)", fontsize=12)
fig.colorbar(s2, ax=axes[1], orientation="horizontal", shrink=0.85, pad=0.03, label="LAI")

s3 = axes[2].scatter(plon[both], plat[both], c=diff[both], s=3,
                     cmap="RdBu_r", vmin=-3, vmax=3, transform=ccrs.PlateCarree())
axes[2].set_title("Difference LM4 − GIMMS, JJA 1982  (bias %.2f, r %.2f)"
                  % (np.nanmean(diff[both]), r), fontsize=12)
fig.colorbar(s3, ax=axes[2], orientation="horizontal", shrink=0.85, pad=0.03, label="ΔLAI")

for ax in axes:
    ax.coastlines(linewidth=0.4)
    ax.set_global()

fig.suptitle("LM4 vs GIMMS LAI4g -- JJA 1982", fontsize=15, y=1.06)
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig("lm4_vs_gimms_lai_jja1982.png", dpi=125)
print("wrote lm4_vs_gimms_lai_jja1982.png")
