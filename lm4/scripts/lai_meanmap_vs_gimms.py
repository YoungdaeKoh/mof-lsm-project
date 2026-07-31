"""MJJAS-mean LAI maps and bias, LM4+ vs GIMMS LAI4g, on common 1-degree cells.

Two windows: the full common period 1982-1996 and the drift-free 1990-1996.
Showing both makes it visible whether the mean-state bias is inherited from the
spin-up adjustment or is a genuine model bias -- the trend analysis
(lai_trend_vs_gimms.py) put the drift entirely before 1990.

Reports the ILAMB-style scores on each window: area-weighted bias, RMSE and the
spatial correlation over the common cells.

Inputs : lm4/data/lm4_lai_1982_1996.npz, lm4/data/gimms_1deg_1982_1996.npz
Output : figures/lai_meanmap_vs_gimms.png, lm4/data/lai_meanmap_scores.csv
"""
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

NLAT, NLON = 180, 360
lat1 = 89.5 - np.arange(NLAT)
lon1 = -179.5 + np.arange(NLON)
WINDOWS = [("1982-1996", np.arange(1982, 1997)),
           ("1990-1996", np.arange(1990, 1997))]

z = np.load("lm4/data/lm4_lai_1982_1996.npz")
g = np.load("lm4/data/gimms_1deg_1982_1996.npz")
lat, lon, keep = z["lat"], z["lon"], z["keep"]
ilat = np.clip(((90.0 - lat) / 1.0).astype(int), 0, NLAT - 1)
ilon = np.clip(((lon + 180.0) / 1.0).astype(int), 0, NLON - 1)


def bin_model(v):
    v = np.where(keep, v, np.nan)
    s = np.zeros((NLAT, NLON))
    c = np.zeros((NLAT, NLON))
    ok = np.isfinite(v)
    np.add.at(s, (ilat[ok], ilon[ok]), v[ok])
    np.add.at(c, (ilat[ok], ilon[ok]), 1.0)
    out = np.full((NLAT, NLON), np.nan)
    m = c > 0
    out[m] = s[m] / c[m]
    return out


W = np.cos(np.deg2rad(lat1))[:, None] * np.ones((1, NLON))
rows, scores = {}, []
for label, yrs in WINDOWS:
    ms = np.stack([bin_model(z["mjjas_%d" % y]) for y in yrs])
    gs = np.stack([g["mjjas_%d" % y] for y in yrs])
    common = np.all(np.isfinite(ms), axis=0) & np.all(np.isfinite(gs), axis=0)
    mm = np.where(common, ms.mean(axis=0), np.nan)
    gg = np.where(common, gs.mean(axis=0), np.nan)
    rows[label] = (mm, gg, common)

    w = np.where(common, W, 0.0)
    wm = np.nansum(np.where(common, mm, 0) * w) / w.sum()
    wg = np.nansum(np.where(common, gg, 0) * w) / w.sum()
    d = mm - gg
    bias = np.nansum(np.where(common, d, 0) * w) / w.sum()
    rmse = np.sqrt(np.nansum(np.where(common, d ** 2, 0) * w) / w.sum())
    a, b = mm[common], gg[common]
    r = np.corrcoef(a, b)[0, 1]
    print("\n=== MJJAS mean, %s, %d common cells ===" % (label, common.sum()))
    print("  LM4 %.3f   GIMMS %.3f   bias %+.3f (%+.1f %%)   RMSE %.3f   r %.3f"
          % (wm, wg, bias, bias / wg * 100, rmse, r))
    print("  cells where model is high: %.1f %%" % (100 * np.mean(d[common] > 0)))
    print("  zonal bias [m2/m2]")
    for a0, a1 in ((60, 85), (30, 60), (0, 30), (-30, 0), (-60, -30)):
        s = common & (lat1[:, None] >= a0) & (lat1[:, None] < a1)
        if s.sum():
            ww = np.where(s, W, 0.0)
            print("    %4d..%-4d  LM4 %5.2f  GIMMS %5.2f  bias %+5.2f"
                  % (a0, a1,
                     np.nansum(np.where(s, mm, 0) * ww) / ww.sum(),
                     np.nansum(np.where(s, gg, 0) * ww) / ww.sum(),
                     np.nansum(np.where(s, d, 0) * ww) / ww.sum()))
    scores.append([int(label[:4]), int(label[-4:]), common.sum(), wm, wg, bias, rmse, r])

np.savetxt("lm4/data/lai_meanmap_scores.csv", np.array(scores), delimiter=",",
           header="y0,y1,ncells,lm4,gimms,bias,rmse,r", comments="", fmt="%.5f")

# ------------------------------------------------------------------ figure ---
LV = np.array([0, 0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0])
LVD = np.array([-3, -2, -1.5, -1, -0.5, -0.2, 0.2, 0.5, 1, 1.5, 2, 3])
proj = ccrs.PlateCarree()
fig, axes = plt.subplots(2, 3, figsize=(16, 6.8), subplot_kw={"projection": proj},
                         constrained_layout=True)
titles = ["LM4+ (model)", "GIMMS LAI4g (obs)", "LM4+ − GIMMS"]
im_val = im_dif = None
for r_, (label, _) in enumerate(WINDOWS):
    mm, gg, common = rows[label]
    for c, (fld, lv, cmap) in enumerate(((mm, LV, "YlGn"), (gg, LV, "YlGn"),
                                         (mm - gg, LVD, "RdBu_r"))):
        ax = axes[r_, c]
        ax.set_extent([-180, 180, -58, 84], crs=proj)
        ax.add_feature(cfeature.COASTLINE, lw=0.4)
        m = ax.contourf(lon1, lat1, np.where(common, fld, np.nan), levels=lv,
                        cmap=cmap, extend="max" if c < 2 else "both", transform=proj)
        if c < 2:
            im_val = m
        else:
            im_dif = m
        ax.set_title("%s  MJJAS  %s" % (label, titles[c]), fontsize=10)
        gl = ax.gridlines(draw_labels=True, lw=0.3, alpha=0.4)
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {"size": 7}
        gl.ylabel_style = {"size": 7}

cb = fig.colorbar(im_val, ax=[axes[1, 0], axes[1, 1]], orientation="horizontal",
                  ticks=LV, shrink=0.7, pad=0.02, aspect=45)
cb.ax.tick_params(labelsize=7)
cb.set_label("LAI [m$^2$/m$^2$]", fontsize=8)
cb2 = fig.colorbar(im_dif, ax=axes[1, 2], orientation="horizontal",
                   ticks=LVD, shrink=0.9, pad=0.02, aspect=25)
cb2.ax.tick_params(labelsize=7)
cb2.set_label("LAI difference [m$^2$/m$^2$]", fontsize=8)
fig.suptitle("MJJAS mean LAI — LM4+ offline (WFDE5) vs GIMMS LAI4g, common 1° cells",
             fontsize=12)
fig.savefig("figures/lai_meanmap_vs_gimms.png", dpi=140, bbox_inches="tight")
print("\nwrote figures/lai_meanmap_vs_gimms.png")
