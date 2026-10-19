#!/usr/bin/env python3
"""SI figure (globe view): why day length depends on latitude and date, shown as the day/night terminator.

Three dates (2010): June solstice, the day 50N first drops below 13 h while days shorten (doy 248, the autumn
leaf-off date of the patch at 50N), and the December solstice. Orthographic globe centred on Siberia; night shaded
with cartopy Nightshade (astronomical solar position); latitude circles 40-70N labelled with the day length from the
patch formula (dayl = 24/pi acos(-tan(lat) tan(decl)), decl = 23.44 sin(2 pi (284 + doy)/365)).
output: ../figures/s1b_daylength_globe.png
"""
import datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature.nightshade import Nightshade

LATS = (40, 50, 60, 70)
COL = {40: "#41ab5d", 50: "#d95f0e", 60: "#7570b3", 70: "#e7298a"}
DATES = [(dt.datetime(2010, 6, 21, 4), "(a) 21 June (solstice)"),
         (dt.datetime(2010, 9, 5, 4), "(b) 5 September (doy 248):\n50°N drops below 13 h → leaf-off"),
         (dt.datetime(2010, 12, 21, 4), "(c) 21 December (solstice)")]


def dayl(lat, doy):
    decl = np.radians(23.44) * np.sin(2 * np.pi * (284 + doy) / 365)
    return 24 / np.pi * np.arccos(np.clip(-np.tan(np.radians(lat)) * np.tan(decl), -1, 1))


proj = ccrs.Orthographic(central_longitude=100, central_latitude=90)   # view from above the North Pole: whole latitude circles visible
fig, axs = plt.subplots(1, 3, figsize=(13, 5.0), subplot_kw={"projection": proj})
for ax, (when, title) in zip(axs, DATES):
    doy = when.timetuple().tm_yday
    ax.set_extent([-180, 180, 25, 90], crs=ccrs.PlateCarree())
    th = np.linspace(0, 2 * np.pi, 200)                              # round frame instead of the clipped octagon
    ax.set_boundary(mpath.Path(np.c_[np.sin(th), np.cos(th)] * 0.5 + 0.5), transform=ax.transAxes)
    ax.add_feature(cfeature.OCEAN, facecolor="#dbe9f6"); ax.add_feature(cfeature.LAND, facecolor="#e9e4d4")
    ax.coastlines(lw=0.4, color="0.4")
    ax.add_feature(Nightshade(when, alpha=0.45))
    ax.gridlines(lw=0.3, color="0.6", ls=":", xlocs=range(-180, 181, 30), ylocs=range(-60, 91, 30))
    lon = np.linspace(-180, 180, 361)
    for lat in LATS:
        # day part of the circle solid, night part dashed (hour angle within +-dayl/2 of local noon)
        sub = np.degrees(np.radians(-15 * (when.hour + when.minute / 60 - 12)))        # sub-solar longitude (approx.)
        ha = ((lon - sub + 180) % 360) - 180
        L = dayl(lat, doy); day = np.abs(ha) <= 7.5 * L
        ax.plot(np.where(day, lon, np.nan), np.full_like(lon, lat), color=COL[lat], lw=2.6, transform=ccrs.PlateCarree())
        ax.plot(np.where(~day, lon, np.nan), np.full_like(lon, lat), color=COL[lat], lw=1.2, ls=(0, (2, 2)), transform=ccrs.PlateCarree())
        ax.text(sub, lat, "%d°N  %.1f h" % (lat, L), transform=ccrs.PlateCarree(), fontsize=8.5, color=COL[lat],
                weight="bold" if (lat == 50 and doy == 248) else None, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.8))
    ax.plot(lon, np.zeros_like(lon), color="0.3", lw=0.8, transform=ccrs.PlateCarree())
    ax.set_title(title, fontsize=10, loc="left")
fig.text(0.5, 0.04, "Viewed from above the North Pole; shaded = night. Each latitude circle is solid on the day side and dotted on the night side:\n"
         "day length = solid fraction \u00d7 24 h. The autumn rule turns leaves off when this falls below 13 h while days are getting shorter.",
         ha="center", fontsize=8.5, color="0.3")
fig.savefig("../figures/s1b_daylength_globe.png", dpi=200, bbox_inches="tight")
print("ok")
