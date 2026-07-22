"""Annual-mean maps (1982) of LM4 land fields on recovered C96 coords.

Unstructured land points -> scatter on PlateCarree. Values already verified
(tropics LAI > boreal). Runoff/evap converted to mm/day.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

z = np.load("maps_1982.npz")
lat, lon = z["lat"], z["lon"]

panels = [
    ("LAI", "LAI (1982 annual mean)", "m$^2$/m$^2$", 1.0, 0, 6, "YlGn"),
    ("runoff", "Runoff", "mm/day", 86400.0, 0, 4, "Blues"),
    ("evap", "Evapotranspiration", "mm/day", 86400.0, 0, 4, "YlGnBu"),
    ("theta_sfc", "Surface soil moisture", "m$^3$/m$^3$", 1.0, 0, 1, "viridis"),
    ("sens", "Sensible heat", "W/m$^2$", 1.0, -20, 80, "RdBu_r"),
    ("soilT_2m", "Soil T at 2 m", "K", 1.0, 250, 305, "inferno"),
]

fig, axes = plt.subplots(3, 2, figsize=(14, 11),
                         subplot_kw={"projection": ccrs.PlateCarree()})
for ax, (k, title, unit, sc, vmin, vmax, cmap) in zip(axes.ravel(), panels):
    v = z[k] * sc
    good = np.isfinite(v)
    scat = ax.scatter(lon[good], lat[good], c=v[good], s=3,
                      cmap=cmap, vmin=vmin, vmax=vmax,
                      transform=ccrs.PlateCarree())
    ax.coastlines(linewidth=0.4)
    ax.set_global()
    ax.set_title(title, fontsize=11)
    cb = fig.colorbar(scat, ax=ax, shrink=0.7, pad=0.02)
    cb.set_label(unit, fontsize=9)

fig.suptitle("LM4 offline spin-up: 1982 annual-mean land fields (WFDE5, C96)",
             fontsize=14, y=0.995)
fig.tight_layout(rect=[0, 0, 1, 0.98])
fig.savefig("lm4_spinup_maps.png", dpi=120)
print("wrote lm4_spinup_maps.png")
