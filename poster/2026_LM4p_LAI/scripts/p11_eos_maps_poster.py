#!/usr/bin/env python3
"""Poster version of the EOS difference maps: two panels side by side, Northern Hemisphere 20-80N.
(a) EOS CTRL - GIMMS, (b) EOS DL14+TC10 - CTRL.  Data: ../data/sos_eos_maps_2010.npz (p8_sos_eos_maps_2010.py).
output: ../figures/fig5_eos_maps_poster.png
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

z = np.load("../data/sos_eos_maps_2010.npz")
lat, lon = z["lat"], z["lon"]
panels = [("(a) EOS 2010: CTRL − GIMMS", z["eos_CTRL"] - z["eos_GIMMS"]), ("(b) EOS 2010: DL14+TC10 − CTRL", z["eos_DL14+T10"] - z["eos_CTRL"])]
proj = ccrs.PlateCarree()
fig, axs = plt.subplots(1, 2, figsize=(16, 3.9), subplot_kw={"projection": proj}, gridspec_kw={"wspace": 0.04})
for ax, (title, d) in zip(axs, panels):
    im = ax.pcolormesh(lon, lat, np.ma.masked_invalid(d), cmap="RdBu_r", vmin=-60, vmax=60, transform=proj, shading="auto")
    ax.coastlines(lw=0.4, color="0.3"); ax.add_feature(cfeature.BORDERS, lw=0.2, edgecolor="0.5")
    ax.set_extent([-180, 180, 20, 80], crs=proj); ax.set_title(title, fontsize=12, loc="left")
    gl = ax.gridlines(draw_labels=True, lw=0.3, color="0.6", ls=":", xlocs=range(-180, 181, 60), ylocs=range(20, 81, 20))
    gl.top_labels = False; gl.right_labels = False; gl.xlabel_style = {"size": 8}; gl.ylabel_style = {"size": 8}
axs[1].gridlines(draw_labels=False)
cb = fig.colorbar(im, ax=axs, orientation="vertical", pad=0.015, shrink=0.85); cb.set_label("Days (+ = later)", fontsize=10)
fig.savefig("../figures/fig5_eos_maps_poster.png", dpi=220, bbox_inches="tight")
