#!/usr/bin/env python3
"""EOS 2010 for all pilot runs (full set, for internal review; the poster shows the diagnostic subset only).

(a) GIMMS EOS (day of year); (b)-(f) model EOS minus GIMMS for CTRL, TC10, DL14+TC10, DL13/12, DLtype.
Northern Hemisphere 20-80N. Data: ../data/sos_eos_maps_2010.npz (p8_sos_eos_maps_2010.py), lat ascending -89.5..89.5.
output: ../figures/fig6_eos_maps_all_runs_2010.png ; band means printed (cos-lat weighted, cells valid in GIMMS and run)
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

z = np.load("../data/sos_eos_maps_2010.npz")
lat, lon = z["lat"], z["lon"]
RUNS = [("CTRL", "CTRL"), ("TC10", "TC10"), ("DL14+T10", "DL14+TC10"), ("DL13/12", "DL13/12"), ("DLtype", "DLtype")]
w = np.cos(np.radians(lat))[:, None] * np.ones_like(z["eos_GIMMS"])
common = np.isfinite(z["eos_GIMMS"])          # same cells for every run, so the band means are comparable
for k, _ in RUNS:
    common &= np.isfinite(z["eos_" + k])
for lo, hi in ((50, 70), (40, 50), (20, 40)):
    band = (lat[:, None] >= lo) & (lat[:, None] < hi)
    row = ["cells %d" % (band & common).sum()]
    for k, lab in RUNS:
        d = z["eos_" + k] - z["eos_GIMMS"]; m = band & common
        row.append("%s %+5.1f" % (lab, np.sum(d[m] * w[m]) / np.sum(w[m])))
    print("%d-%dN  EOS model-GIMMS (d): %s" % (lo, hi, " | ".join(row)))

proj = ccrs.PlateCarree()
fig, axs = plt.subplots(3, 2, figsize=(16, 6.4), subplot_kw={"projection": proj}, gridspec_kw={"hspace": 0.28, "wspace": 0.06})
fig.subplots_adjust(left=0.04, right=0.98, top=0.92, bottom=0.16)
panels = [("(a) GIMMS EOS 2010 (day of year)", z["eos_GIMMS"], "viridis", 180, 330)]
panels += [("(%s) %s − GIMMS" % ("bcdef"[i], lab), z["eos_" + k] - z["eos_GIMMS"], "RdBu_r", -60, 60) for i, (k, lab) in enumerate(RUNS)]
for ax, (title, d, cmap, lo, hi) in zip(axs.flat, panels):
    im = ax.pcolormesh(lon, lat, np.ma.masked_invalid(d), cmap=cmap, vmin=lo, vmax=hi, transform=proj, shading="auto")
    ax.coastlines(lw=0.4, color="0.3"); ax.add_feature(cfeature.BORDERS, lw=0.2, edgecolor="0.5")
    ax.set_extent([-170, 180, 20, 80], crs=proj); ax.set_title(title, fontsize=11, loc="left")
    gl = ax.gridlines(draw_labels=True, lw=0.3, color="0.6", ls=":", xlocs=range(-180, 181, 60), ylocs=range(20, 81, 20))
    gl.top_labels = False; gl.right_labels = False; gl.xlabel_style = {"size": 8}; gl.ylabel_style = {"size": 8}
    if title.startswith("(a)"):
        cb_a = im
    else:
        cb_d = im
# horizontal colour bars under the panels: left = (a) day of year, right = (b)-(f) difference
fig.colorbar(cb_a, cax=fig.add_axes([0.08, 0.07, 0.36, 0.022]), orientation="horizontal", label="(a) Day of year")
fig.colorbar(cb_d, cax=fig.add_axes([0.56, 0.07, 0.36, 0.022]), orientation="horizontal", extend="both", label="(b)–(f) Days (+ = later than GIMMS)")
fig.suptitle("End of season (EOS) 2010, 50 % amplitude of monthly LAI: all pilot runs", fontsize=12, y=0.99)
fig.savefig("../figures/fig6_eos_maps_all_runs_2010.png", dpi=170, bbox_inches="tight")
print("wrote ../figures/fig6_eos_maps_all_runs_2010.png")
