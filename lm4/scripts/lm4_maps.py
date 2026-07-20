# LM4 last-30yr (spin-up yr 271-300) seasonal-mean maps. C96 cell centers (verified).
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
try:
    import cartopy.crs as ccrs, cartopy.feature as cfeature
    HAVE_CARTO = True
except Exception as e:
    HAVE_CARTO = False; print("no cartopy:", e)

D = np.load("/Volumes/data01/MOF_LSM_project/lm4/data/seasmap_last30.npz")
lat, lon = D["lat"], D["lon"]
SEAS = ["DJF", "MAM", "JJA", "SON"]

# (key, label, cmap, scale, unit)
VARS = [
    ("soilT_top",  "Near-surface soil T (top ~0.01 m)", "turbo", 1.0,   "K"),
    ("soilT_deep", "Deep soil T (~2 m)",                "turbo", 1.0,   "K"),
    ("sens",       "Sensible heat flux",                "RdYlBu_r", 1.0, "W m$^{-2}$"),
    ("evap",       "Evaporation",                       "YlGnBu", 86400.0, "mm day$^{-1}$"),
    ("LAI",        "LAI",                               "YlGn",  1.0,   "m$^2$ m$^{-2}$"),
]

for key, label, cmap, scale, unit in VARS:
    allv = np.concatenate([D[f"{key}_{s}"] * scale for s in SEAS])
    vmin, vmax = np.nanpercentile(allv, [2, 98])
    proj = ccrs.PlateCarree() if HAVE_CARTO else None
    fig, axes = plt.subplots(2, 2, figsize=(15, 8),
                             subplot_kw={"projection": proj} if HAVE_CARTO else None)
    fig.suptitle(f"LM4 WFDE5 dynveg spin-up — last-30yr (yr 271-300) seasonal mean: {label}",
                 fontsize=13, fontweight="bold")
    for ax, s in zip(axes.flat, SEAS):
        v = D[f"{key}_{s}"] * scale
        if HAVE_CARTO:
            ax.set_global(); ax.coastlines(lw=0.4, color="0.3")
            sc = ax.scatter(lon, lat, c=v, s=4, cmap=cmap, vmin=vmin, vmax=vmax,
                            transform=ccrs.PlateCarree())
        else:
            sc = ax.scatter(lon, lat, c=v, s=4, cmap=cmap, vmin=vmin, vmax=vmax)
            ax.set_xlim(-180, 180); ax.set_ylim(-90, 90)
        ax.set_title(s, fontsize=11, fontweight="bold")
    cbar = fig.colorbar(sc, ax=axes, orientation="horizontal", fraction=0.045, pad=0.05, shrink=0.6)
    cbar.set_label(unit)
    out = f"/Volumes/data01/MOF_LSM_project/figures/lm4_seasmap_{key}.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {out}  vmin={vmin:.3g} vmax={vmax:.3g}")
