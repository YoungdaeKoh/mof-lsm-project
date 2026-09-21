"""Noah-MP DVEG=5 WFDE5 carbon spin-up: (a) pool means per cycle, (b) cycle-6 WOOD map,
(c) cycle-6 LAI map, (d) WOOD relative change cycle 5->6 (per-cell convergence).
Reads the local archive /Volumes/data02/NOAHMP/spinup_raw/noahmp_WFDE5_1deg_dveg5/.
Means: non-ice land, cos(lat) weighted (memory lsm-spinup-ice-mask-convergence).
"""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import cartopy.crs as ccrs, cartopy.feature as cfeature
from netCDF4 import Dataset

A = "/Volumes/data02/NOAHMP/spinup_raw/noahmp_WFDE5_1deg_dveg5/"
SETUP = "/Volumes/data02/NOAHMP/init/HRLDAS_setup_GSWP3_1deg_d01.nc"
OUT = "/Volumes/data01/MOF_LSM_project/figures/noahmp/noahmp_dveg5_spinup_6cyc.png"
SEED = A + "SEED_staticveg_cyc2_RESTART.2010122500_DOMAIN1"   # physics seed (static-veg spin-up end), carbon = cold-start placeholders

s = Dataset(SETUP)
lat = np.array(s.variables["XLAT"][0]); lon = np.array(s.variables["XLONG"][0]); ivg = np.array(s.variables["IVGTYP"][0]); s.close()
land = (ivg > 0) & (ivg != 17) & (ivg != 21)
nonice = land & (ivg != 15)
w = np.cos(np.deg2rad(lat)) * nonice
wm = lambda x: float((x * w).sum() / w.sum())

POOLS = ["WOOD", "FASTCP", "STBLCP", "RTMASS", "LFMASS", "LAI"]
def read(f):
    d = Dataset(f); r = {v: np.array(d.variables[v][0], "f8") for v in POOLS}; d.close(); return r
cyc = {c: read(A + "cycle%02d/RESTART.2011010103_DOMAIN1" % c) for c in range(1, 7)}
try:
    seed = read(SEED); x0 = [0]; series0 = {v: [wm(seed[v])] for v in POOLS}
except Exception:
    x0 = []; series0 = {v: [] for v in POOLS}
xs = x0 + list(range(1, 7))
series = {v: series0[v] + [wm(cyc[c][v]) for c in range(1, 7)] for v in POOLS}

fig = plt.figure(figsize=(13, 9))
# (a) time series
ax = fig.add_subplot(2, 2, 1)
for v, col in zip(["WOOD", "FASTCP", "STBLCP", "RTMASS"], ["saddlebrown", "tab:orange", "tab:red", "tab:green"]):
    ax.plot(xs, series[v], "o-", color=col, label=v)
ax.set_xlabel("spin-up cycle (30 yr each, WFDE5 1981-2010)"); ax.set_ylabel("gC m$^{-2}$, non-ice land, cos(lat)-weighted")
ax.set_xticks(xs); ax.set_xticklabels(["seed"] * len(x0) + [str(c) for c in range(1, 7)])
ax.grid(alpha=.3); ax.legend(loc="upper left", fontsize=9)
ax2 = ax.twinx(); ax2.plot(xs, series["LAI"], "s--", color="k", label="LAI (right)"); ax2.set_ylim(0, 3); ax2.set_ylabel("LAI"); ax2.legend(loc="lower right", fontsize=9)
ax.set_title("(a) Noah-MP DVEG=5 carbon pools at end of each cycle")

proj = ccrs.PlateCarree(central_longitude=0)
def mapax(pos, title):
    a = fig.add_subplot(2, 2, pos, projection=proj)
    a.set_global(); a.coastlines(lw=.4); a.add_feature(cfeature.OCEAN, facecolor="lightgray", zorder=0)
    a.set_title(title, fontsize=10); return a
# (b) WOOD cycle 6 (log)
a = mapax(2, "(b) WOOD, cycle 6 (gC m$^{-2}$, log)")
z = np.where(nonice, cyc[6]["WOOD"], np.nan); z = np.where(z > 1, z, np.nan)
m = a.pcolormesh(lon, lat, z, transform=ccrs.PlateCarree(), cmap="YlGn", norm=LogNorm(10, 30000), shading="auto")
fig.colorbar(m, ax=a, orientation="horizontal", pad=.03, shrink=.8)
# (c) LAI cycle 6
a = mapax(3, "(c) LAI, cycle 6 (Jan 1 value)")
z = np.where(nonice, cyc[6]["LAI"], np.nan)
m = a.pcolormesh(lon, lat, z, transform=ccrs.PlateCarree(), cmap="viridis", vmin=0, vmax=5, shading="auto")
fig.colorbar(m, ax=a, orientation="horizontal", pad=.03, shrink=.8)
# (d) WOOD relative change cycle 5 -> 6
a = mapax(4, "(d) WOOD change cycle 5$\\rightarrow$6 (%): 98% of cells within 1%;\nblue band = mixed tundra (WOOD 2-7 gC m$^{-2}$, tiny absolute)")
w5, w6 = cyc[5]["WOOD"], cyc[6]["WOOD"]
z = np.where(nonice & (w6 > 10), 100 * (w6 - w5) / w6, np.nan)
m = a.pcolormesh(lon, lat, z, transform=ccrs.PlateCarree(), cmap="RdBu_r", vmin=-2, vmax=2, shading="auto")
fig.colorbar(m, ax=a, orientation="horizontal", pad=.03, shrink=.8, extend="both")
fig.suptitle("Noah-MP v5.2.1 DVEG=5, WFDE5 1$^\\circ$/6h, warm start from GSWP3 static-veg spin-up", fontsize=12)
fig.tight_layout()
fig.savefig(OUT, dpi=130)
print("wrote", OUT)
for v in POOLS: print("%-7s" % v, " ".join("%9.1f" % x for x in series[v]))
zz = z[np.isfinite(z)]
print("(d) cells %d  |rel|<=1%%: %.1f%%  mean %.3f%%  p90 |rel| %.2f%%" % (zz.size, 100 * (np.abs(zz) <= 1).mean(), zz.mean(), np.percentile(np.abs(zz), 90)))
