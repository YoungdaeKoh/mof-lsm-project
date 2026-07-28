"""Verify the 1-deg LAI comparison: scatter + difference map."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

z = np.load("lai_1deg_1982_1986.npz")
lat, lon, lm4, gimms = z["lat"], z["lon"], z["lm4"], z["gimms"]
both = np.isfinite(lm4) & np.isfinite(gimms)
lm4v, gv = lm4[both], gimms[both]
bias = np.mean(lm4v - gv)
rmse = np.sqrt(np.mean((lm4v - gv) ** 2))
r = np.corrcoef(lm4v, gv)[0, 1]

lon2d, lat2d = np.meshgrid(lon, lat)
diff = lm4 - gimms

fig = plt.figure(figsize=(16, 5))

# scatter (density-ish via alpha)
ax0 = fig.add_subplot(1, 3, 1)
ax0.scatter(gv, lm4v, s=4, alpha=0.15, color="#2c6fbb")
ax0.plot([0, 7], [0, 7], "k--", lw=1)
ax0.set_xlabel("GIMMS LAI"); ax0.set_ylabel("LM4 LAI")
ax0.set_xlim(0, 7); ax0.set_ylim(0, 7)
ax0.set_title("1:1 scatter  (n=%d, r=%.2f)\nbias=%+.2f  RMSE=%.2f"
              % (both.sum(), r, bias, rmse), fontsize=10)
ax0.grid(alpha=0.3)

axm = fig.add_subplot(1, 3, 2, projection=ccrs.PlateCarree())
pm = axm.pcolormesh(lon2d, lat2d, diff, cmap="RdBu_r", vmin=-3, vmax=3,
                    transform=ccrs.PlateCarree(), shading="auto")
axm.coastlines(linewidth=0.4); axm.set_global()
axm.set_title("LM4 - GIMMS (JJA 1982-1986)", fontsize=10)
fig.colorbar(pm, ax=axm, orientation="horizontal", shrink=0.8, pad=0.03, label="ΔLAI")

# zonal-mean profile (teaches where bias lives)
axz = fig.add_subplot(1, 3, 3)
zlm4 = np.nanmean(np.where(both, lm4, np.nan), axis=1)
zgim = np.nanmean(np.where(both, gimms, np.nan), axis=1)
axz.plot(zlm4, lat, "-", color="#4a9d47", label="LM4")
axz.plot(zgim, lat, "-", color="#888", label="GIMMS")
axz.set_xlabel("zonal-mean LAI"); axz.set_ylabel("latitude")
axz.set_ylim(-60, 80); axz.legend(fontsize=9); axz.grid(alpha=0.3)
axz.set_title("Zonal mean", fontsize=10)

fig.suptitle("LM4 vs GIMMS LAI4g (datakit, native 1/12° -> common 1°) JJA 1982-1986",
             fontsize=12, y=1.02)
fig.tight_layout()
fig.savefig("lai_1deg_compare.png", dpi=130, bbox_inches="tight")
print("wrote lai_1deg_compare.png")
