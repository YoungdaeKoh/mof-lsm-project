"""LM4 vs GIMMS LAI4g, JJA 1982-1986 (5-year mean, matched years).

Top row: LM4 mean, GIMMS mean, difference (3 maps).
Bottom: per-year bias and spatial correlation, to show consistency.
"""
import numpy as np
import netCDF4 as nc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

YEARS = [1982, 1983, 1984, 1985, 1986]

# --- LM4 ---
z = np.load("lm4_lai_jja_1982_1986.npz")
plat, plon = z["lat"], z["lon"]
lm4_yr = {y: z["lai_%d" % y] for y in YEARS}
lm4_mean = np.nanmean(np.stack([lm4_yr[y] for y in YEARS]), axis=0)

# --- GIMMS (time idx0 = 1982-01); JJA of year Y = (Y-1982)*12 + [5,6,7] ---
d = nc.Dataset("/Volumes/data02/LAI/GIMMS_LAI4g_V1.2_1982_2020.nc")
glat = d.variables["latitude"][:]
glon = d.variables["longitude"][:]
gimms_yr = {}
for y in YEARS:
    b = (y - 1982) * 12
    G = np.stack([np.ma.filled(d.variables["lai"][b + m].astype("f8"), np.nan)
                  for m in (5, 6, 7)])
    G[G > 100] = np.nan
    gimms_yr[y] = np.nanmean(G, axis=0)
d.close()
gimms_mean = np.nanmean(np.stack([gimms_yr[y] for y in YEARS]), axis=0)

# nearest-cell sampler
lon360 = np.where(plon < 0, plon + 360, plon)
ilat = np.clip(np.round((plat - glat[0]) / 0.5).astype(int), 0, len(glat) - 1)
ilon = (np.round((lon360 - glon[0]) / 0.5).astype(int)) % len(glon)

def sample(field):
    return field[ilat, ilon]

gsamp_mean = sample(gimms_mean)
diff = lm4_mean - gsamp_mean
both = np.isfinite(diff)

# per-year stats
print("year   bias   corr")
biases, corrs = [], []
for y in YEARS:
    gs = sample(gimms_yr[y])
    dd = lm4_yr[y] - gs
    m = np.isfinite(dd)
    b = np.nanmean(dd[m])
    r = np.corrcoef(lm4_yr[y][m], gs[m])[0, 1]
    biases.append(b); corrs.append(r)
    print("%d  %+.3f  %.3f" % (y, b, r))
bias5 = np.nanmean(diff[both])
r5 = np.corrcoef(lm4_mean[both], gsamp_mean[both])[0, 1]
print("5yr mean bias=%+.3f corr=%.3f" % (bias5, r5))

# --- figure ---
fig = plt.figure(figsize=(20, 8))
proj = ccrs.PlateCarree()

ax1 = fig.add_subplot(2, 3, 1, projection=proj)
s1 = ax1.scatter(plon, plat, c=lm4_mean, s=3, cmap="YlGn", vmin=0, vmax=6, transform=proj)
ax1.set_title("LM4 offline LAI (JJA 1982-1986)", fontsize=11)
fig.colorbar(s1, ax=ax1, orientation="horizontal", shrink=0.85, pad=0.03, label="LAI")

ax2 = fig.add_subplot(2, 3, 2, projection=proj)
lon2d, lat2d = np.meshgrid(glon, glat)
s2 = ax2.pcolormesh(lon2d, lat2d, gimms_mean, cmap="YlGn", vmin=0, vmax=6,
                    transform=proj, shading="auto")
ax2.set_title("GIMMS LAI4g (JJA 1982-1986)", fontsize=11)
fig.colorbar(s2, ax=ax2, orientation="horizontal", shrink=0.85, pad=0.03, label="LAI")

ax3 = fig.add_subplot(2, 3, 3, projection=proj)
s3 = ax3.scatter(plon[both], plat[both], c=diff[both], s=3, cmap="RdBu_r",
                 vmin=-3, vmax=3, transform=proj)
ax3.set_title("Difference LM4 - GIMMS  (bias %+.2f, r %.2f)" % (bias5, r5), fontsize=11)
fig.colorbar(s3, ax=ax3, orientation="horizontal", shrink=0.85, pad=0.03, label="ΔLAI")

for ax in (ax1, ax2, ax3):
    ax.coastlines(linewidth=0.4); ax.set_global()

# per-year consistency
axb = fig.add_subplot(2, 3, 4)
axb.bar([str(y) for y in YEARS], biases, color="#c0504d")
axb.axhline(0, color="k", lw=0.6)
axb.set_title("Per-year bias (LM4 - GIMMS)", fontsize=11)
axb.set_ylabel("ΔLAI"); axb.grid(alpha=0.3, axis="y")

axc = fig.add_subplot(2, 3, 5)
axc.plot([str(y) for y in YEARS], corrs, "-o", color="#2c6fbb")
axc.set_ylim(0.5, 0.75)
axc.set_title("Per-year spatial correlation", fontsize=11)
axc.set_ylabel("r"); axc.grid(alpha=0.3)

axt = fig.add_subplot(2, 3, 6)
axt.plot([str(y) for y in YEARS], [np.nanmean(lm4_yr[y]) for y in YEARS],
         "-o", label="LM4", color="#4a9d47")
axt.plot([str(y) for y in YEARS],
         [np.nanmean(sample(gimms_yr[y])[both]) for y in YEARS],
         "-s", label="GIMMS", color="#888")
axt.set_title("Global-mean LAI trend", fontsize=11)
axt.set_ylabel("LAI"); axt.legend(); axt.grid(alpha=0.3)

fig.suptitle("LM4 vs GIMMS LAI4g -- JJA, 5-year mean (1982-1986)", fontsize=14, y=1.0)
fig.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig("lm4_vs_gimms_lai_jja_5yr.png", dpi=120)
print("wrote lm4_vs_gimms_lai_jja_5yr.png")
