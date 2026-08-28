"""Report figure: root-zone soil temperature, LM4+ against ERA5-Land.

The full comparison covers four layers down to 2.89 m (soilT_vs_era5land.py), but
eight panels do not survive a page width, and the root zone is the depth the
project is actually about -- it is what the vegetation draws on and what couples
to the atmosphere.

Root zone is taken as 0-100 cm, which ERA5-Land's first three layers tile
exactly: 0-7, 7-28 and 28-100 cm, so the weights are the layer thicknesses
(0.07, 0.21, 0.72). The deeper layer and its high-latitude signal stay in the
table.

Two panels, because the mean and the amplitude say different things: the mean
bias largely follows the forcing air temperature, while the amplitude of the
annual cycle is about how the model moves heat through the column.

Input : lm4/data/soilT_clim_1deg.npz (written by soilT_vs_era5land.py)
Output: figures/report_soilT_rootzone.png
"""
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# report figures carry Korean labels; without this the glyphs render as boxes
matplotlib.rcParams["font.family"] = "AppleGothic"
matplotlib.rcParams["axes.unicode_minus"] = False    # AppleGothic has no U+2212

NLAT, NLON = 180, 360
lat1 = 89.5 - np.arange(NLAT)
lon1 = -179.5 + np.arange(NLON)
W_LAYER = np.array([0.07, 0.21, 0.72])          # 0-7, 7-28, 28-100 cm

c = np.load("lm4/data/soilT_clim_1deg.npz")
lm = np.einsum("l,lmyx->myx", W_LAYER, c["lm4"][:3].astype("f8"))
er = np.einsum("l,lmyx->myx", W_LAYER, c["era5"][:3].astype("f8"))

lm_ann, er_ann = lm.mean(axis=0), er.mean(axis=0)
lm_amp = lm.max(axis=0) - lm.min(axis=0)
er_amp = er.max(axis=0) - er.min(axis=0)
sel = np.isfinite(lm_ann) & np.isfinite(er_ann)
W = np.cos(np.deg2rad(lat1))[:, None] * np.ones((1, NLON))
w = np.where(sel, W, 0.0)

mm = np.nansum(np.where(sel, lm_ann, 0) * w) / w.sum()
ee = np.nansum(np.where(sel, er_ann, 0) * w) / w.sum()
rmse = np.sqrt(np.nansum(np.where(sel, (lm_ann - er_ann) ** 2, 0) * w) / w.sum())
r = np.corrcoef(lm_ann[sel], er_ann[sel])[0, 1]
ma = np.nansum(np.where(sel, lm_amp, 0) * w) / w.sum()
ea = np.nansum(np.where(sel, er_amp, 0) * w) / w.sum()
print("root zone 0-100 cm, %d cells" % sel.sum())
print("  LM4 %.2f  ERA5-Land %.2f  bias %+.2f K  RMSE %.2f  r %.3f"
      % (mm, ee, mm - ee, rmse, r))
print("  annual amplitude  LM4 %.2f  ERA5-Land %.2f  ratio %.3f" % (ma, ea, ma / ea))
print("\n%-10s %8s %8s %9s" % ("band", "bias", "amp ratio", "cells"))
for a0, a1 in ((60, 85), (30, 60), (0, 30), (-30, 0), (-60, -30)):
    b = sel & (lat1[:, None] >= a0) & (lat1[:, None] < a1)
    if b.sum() < 20:
        continue
    ww = np.where(b, W, 0.0)
    bi = (np.nansum(np.where(b, lm_ann - er_ann, 0) * ww) / ww.sum())
    ra = (np.nansum(np.where(b, lm_amp, 0) * ww) / ww.sum()
          / (np.nansum(np.where(b, er_amp, 0) * ww) / ww.sum()))
    print("%4d..%-4d %+8.2f %9.3f %9d" % (a0, a1, bi, ra, b.sum()))

# ------------------------------------------------------------------ figure --
proj = ccrs.PlateCarree()
# stacked, not side by side: on a page the two-column version leaves each map
# about 8 cm wide, which is too small to read the high-latitude band
fig, axes = plt.subplots(2, 1, figsize=(9.5, 8.6), subplot_kw={"projection": proj},
                         constrained_layout=True)
PANELS = [
    # ASCII hyphen, not U+2212: AppleGothic has no glyph for the typographic minus
    (np.where(sel, lm_ann - er_ann, np.nan),
     np.array([-6, -4, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 4, 6]), "RdBu_r",
     "(a) 연평균 편차  LM4+ - ERA5-Land  [K]"),
    (np.where(sel & (er_amp > 0.5), lm_amp / er_amp, np.nan),
     np.array([0.6, 0.75, 0.85, 0.92, 0.97, 1.03, 1.08, 1.15, 1.3, 1.5]), "PuOr_r",
     "(b) 연진폭 비  LM4+ / ERA5-Land  (1 미만 = 과소)"),
]
for ax, (fld, lv, cmap, ttl) in zip(axes, PANELS):
    ax.set_extent([-180, 180, -58, 84], crs=proj)
    ax.add_feature(cfeature.COASTLINE, lw=0.4)
    im = ax.contourf(lon1, lat1, fld, levels=lv, cmap=cmap, extend="both",
                     transform=proj)
    ax.set_title(ttl, fontsize=13, loc="left")
    gl = ax.gridlines(draw_labels=True, lw=0.3, alpha=0.4)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {"size": 9}
    gl.ylabel_style = {"size": 9}
    cb = fig.colorbar(im, ax=ax, orientation="horizontal", ticks=lv,
                      shrink=0.92, pad=0.03, aspect=32)
    cb.ax.tick_params(labelsize=9)

fig.suptitle("근권(0–100 cm) 토양온도 1990–2010 — LM4+ vs ERA5-Land, 공통 1° 격자\n"
             "편차 %+.2f K · RMSE %.2f K · r %.3f · 진폭비 %.2f"
             % (mm - ee, rmse, r, ma / ea), fontsize=13)
fig.savefig("figures/report_soilT_rootzone.png", dpi=150, bbox_inches="tight")
print("\nwrote figures/report_soilT_rootzone.png")
