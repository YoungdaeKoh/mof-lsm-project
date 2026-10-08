# Figures for the snow diagnostics (2001-2023, NH land 20-90N, common ice/perennial mask; see notes/decisions.md)
#   fig_snow_seasonal_cycle.png : NH-mean monthly SWE and SCF, 4 LSMs vs ERA5-Land / MODIS
#   fig_snow_swe_bias_MAM.png   : MAM SWE bias (model - ERA5-Land) on each model's native grid
import numpy as np, xarray as xr
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs, cartopy.feature as cfeature

D = "/Volumes/data02/MOF_LSM_model_results/snowdiag/"
FIG = "/Volumes/data01/MOF_LSM_project/figures/snow/"
MODELS = ["LM4p", "CLM5", "NoahMP", "JULES"]
LABEL = {"LM4p": "LM4+", "CLM5": "CLM5", "NoahMP": "Noah-MP", "JULES": "JULES"}
COL = {"LM4p": "#1b9e77", "CLM5": "#d95f02", "NoahMP": "#7570b3", "JULES": "#e7298a"}
MINUS = "−"
import os; os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.size": 11, "axes.unicode_minus": True})

# ---------- Fig 1: seasonal cycle ----------
c = xr.open_dataset(D + "snow_seasonal_cycle_2001_2023_perm100.nc")
mon = np.arange(1, 13)
fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
for ax, var, unit, obsname in ((axs[0], "SWE", "mm", "ERA5-Land"), (axs[1], "SCF", "fraction", "MODIS")):
    obs = np.mean([c[f"{n}_{var}_obs"].values for n in MODELS], 0)  # obs on the 4 model grids differ < 1 mm / 0.004
    ax.plot(mon, obs, color="k", lw=2.5, label=obsname)
    for n in MODELS:
        ax.plot(mon, c[f"{n}_{var}_model"].values, color=COL[n], lw=1.6, marker="o", ms=3, label=LABEL[n])
    ax.set_xticks(mon); ax.set_xticklabels(list("JFMAMJJASOND")); ax.set_xlim(0.5, 12.5)
    ax.set_ylabel(f"{var} ({unit})"); ax.grid(alpha=0.3)
    ax.set_title(f"({'ab'[var == 'SCF']}) NH land 20–90N {var}", loc="left")
axs[0].legend(frameon=False, fontsize=9)
fig.text(0.5, -0.02, "2001–2023 climatology; Greenland/Antarctic ice and perennial-snow cells masked "
         "(IGBP snow/ice ≥ 50 % or Aug SWE > 100 mm); cos(lat) weighted, each model on its native grid",
         ha="center", fontsize=8.5)
fig.tight_layout(); fig.savefig(FIG + "fig_snow_seasonal_cycle.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ---------- Fig 2: MAM SWE bias maps ----------
met = {}
for line in open(D + "snow_metrics_2001_2023_perm100.txt"):
    if line.startswith("#"): continue
    p = line.split()
    if p[1] == "NH" and p[2] == "MAM" and p[3] == "SWE":
        met[p[0]] = (float(p[8]), float(p[10]))  # bias %, spatial r
lev = [-150, -100, -60, -30, -10, 10, 30, 60, 100, 150]
cmap = plt.get_cmap("RdBu", len(lev) + 1)  # red = too little snow, blue = too much
norm = mcolors.BoundaryNorm(lev, cmap.N, extend="both")
proj = ccrs.NorthPolarStereo(central_longitude=100)
import matplotlib.path as mpath
_th = np.linspace(0, 2 * np.pi, 200)
circle = mpath.Path(np.vstack([np.sin(_th), np.cos(_th)]).T * 0.5 + 0.5)
fig, axs = plt.subplots(2, 2, figsize=(10, 10), subplot_kw=dict(projection=proj))
for ax, n in zip(axs.ravel(), MODELS):
    s = xr.open_dataset(D + f"snow_seasclim_{n}_perm100.nc")
    b = (s.SWE_MAM_model - s.SWE_MAM_obs).where(s.lat >= 20)
    ax.set_extent([0, 359.9, 20, 90], ccrs.PlateCarree())
    ax.add_feature(cfeature.LAND, facecolor="0.85", zorder=0)  # masked land (ice, perennial snow) shows grey
    pm = ax.pcolormesh(s.lon, s.lat, b, cmap=cmap, norm=norm, shading="nearest", transform=ccrs.PlateCarree())
    ax.coastlines(lw=0.4)
    gl = ax.gridlines(lw=0.3, color="0.5", ylocs=[30, 45, 60, 75])
    bp, r = met[n]
    ax.set_boundary(circle, transform=ax.transAxes)
    ax.set_title(LABEL[n] + f"   bias {bp:+.0f} %".replace("-", MINUS) + f"   r = {r:.2f}", fontsize=12)
cb = fig.colorbar(pm, ax=axs, orientation="horizontal", fraction=0.04, pad=0.04, ticks=lev)
cb.ax.set_xticklabels([f"{v}".replace("-", MINUS) for v in lev])
cb.set_label("MAM SWE bias, model − ERA5-Land (mm), 2001–2023")
fig.savefig(FIG + "fig_snow_swe_bias_MAM.png", dpi=200, bbox_inches="tight"); plt.close(fig)
print("saved", FIG)
