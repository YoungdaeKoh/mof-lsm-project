"""Per-cell LAI trend maps, LM4+ vs GIMMS LAI4g, over the common period 1982-1996.

The global-mean comparison (lai_trend_vs_gimms.py) showed the model rising 2.4x
faster than the observations before 1990 and flat afterwards.  This asks where
that happens: trends are fitted cell by cell on the common 1-degree grid, so the
drift can be attributed to particular biomes instead of a single global number.

Trends are m2/m2 per decade.  Cells enter only if both fields are valid in all
fifteen years; zonal profiles use cos(lat) weights.

Inputs : lm4/data/lm4_lai_1982_1996.npz, lm4/data/gimms_1deg_1982_1996.npz
Output : figures/lai_trendmap_vs_gimms.png, lm4/data/lai_trendmap_zonal.csv
"""
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

YEARS = np.arange(1982, 1997)
NLAT, NLON = 180, 360
lat1 = 89.5 - np.arange(NLAT)          # descending
lon1 = -179.5 + np.arange(NLON)

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


def trend(stack):
    """Least-squares slope per cell, per decade."""
    t = YEARS - YEARS.mean()
    den = (t ** 2).sum()
    an = stack - stack.mean(axis=0)
    return (an * t[:, None, None]).sum(axis=0) / den * 10.0


W = np.cos(np.deg2rad(lat1))[:, None] * np.ones((1, NLON))
rows = {}
for win in ("ann", "mjjas"):
    ms = np.stack([bin_model(z["%s_%d" % (win, y)]) for y in YEARS])
    gs = np.stack([g["%s_%d" % (win, y)] for y in YEARS])
    common = np.all(np.isfinite(ms), axis=0) & np.all(np.isfinite(gs), axis=0)
    tm = np.where(common, trend(np.where(common, ms, 0.0)), np.nan)
    tg = np.where(common, trend(np.where(common, gs, 0.0)), np.nan)
    rows[win] = (tm, tg, common)

    w = np.where(common, W, 0.0)
    am = np.nansum(np.where(common, tm, 0) * w) / w.sum()
    ag = np.nansum(np.where(common, tg, 0) * w) / w.sum()
    print("\n=== %s, 1982-1996, %d common cells ===" % (win, common.sum()))
    print("  area-weighted mean trend   LM4 %+.4f   GIMMS %+.4f  (m2/m2 per decade)"
          % (am, ag))
    print("  cells with positive trend  LM4 %5.1f%%   GIMMS %5.1f%%"
          % (100 * np.nanmean(tm[common] > 0), 100 * np.nanmean(tg[common] > 0)))
    print("  |trend| p98                LM4 %.3f    GIMMS %.3f"
          % (np.nanpercentile(np.abs(tm[common]), 98),
             np.nanpercentile(np.abs(tg[common]), 98)))
    d = tm - tg
    print("  model minus obs: mean %+.4f, cells where model is more positive %.1f%%"
          % (np.nansum(np.where(common, d, 0) * w) / w.sum(),
             100 * np.nanmean(d[common] > 0)))
    print("  zonal mean trend [m2/m2/decade]")
    print("    band        LM4     GIMMS   diff")
    for a0, a1 in ((60, 85), (30, 60), (0, 30), (-30, 0), (-60, -30)):
        s = common & (lat1[:, None] >= a0) & (lat1[:, None] < a1)
        if s.sum():
            ww = np.where(s, W, 0.0)
            vm = np.nansum(np.where(s, tm, 0) * ww) / ww.sum()
            vg = np.nansum(np.where(s, tg, 0) * ww) / ww.sum()
            print("    %4d..%-4d %+7.4f %+7.4f %+7.4f" % (a0, a1, vm, vg, vm - vg))

# ------------------------------------------------------------------ figure ---
LV = np.array([-0.6, -0.4, -0.25, -0.15, -0.05, 0.05, 0.15, 0.25, 0.4, 0.6])
LVD = np.array([-0.6, -0.4, -0.25, -0.15, -0.05, 0.05, 0.15, 0.25, 0.4, 0.6])
proj = ccrs.PlateCarree()
fig, axes = plt.subplots(2, 3, figsize=(16, 6.8), subplot_kw={"projection": proj},
                         constrained_layout=True)
titles = ["LM4+ (model)", "GIMMS LAI4g (obs)", "LM4+ − GIMMS"]
im_val = im_dif = None
for r, win in enumerate(("ann", "mjjas")):
    tm, tg, common = rows[win]
    for c, (fld, lv, cmap) in enumerate(((tm, LV, "BrBG"), (tg, LV, "BrBG"),
                                         (tm - tg, LVD, "RdBu_r"))):
        ax = axes[r, c]
        ax.set_extent([-180, 180, -58, 84], crs=proj)
        ax.add_feature(cfeature.COASTLINE, lw=0.4)
        m = ax.contourf(lon1, lat1, np.where(common, fld, np.nan), levels=lv,
                        cmap=cmap, extend="both", transform=proj)
        if c < 2:
            im_val = m
        else:
            im_dif = m
        ax.set_title("%s  %s" % ("Jan-Nov" if win == "ann" else "MJJAS",
                                 titles[c]), fontsize=10)
        gl = ax.gridlines(draw_labels=True, lw=0.3, alpha=0.4)
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {"size": 7}
        gl.ylabel_style = {"size": 7}

cb = fig.colorbar(im_val, ax=[axes[1, 0], axes[1, 1]], orientation="horizontal",
                  ticks=LV, shrink=0.7, pad=0.02, aspect=45)
cb.ax.tick_params(labelsize=7)
cb.set_label("LAI trend [m$^2$/m$^2$ per decade]", fontsize=8)
cb2 = fig.colorbar(im_dif, ax=axes[1, 2], orientation="horizontal",
                   ticks=LVD, shrink=0.9, pad=0.02, aspect=25)
cb2.ax.tick_params(labelsize=7)
cb2.set_label("trend difference [m$^2$/m$^2$ per decade]", fontsize=8)
fig.suptitle("LAI trend 1982–1996, common 1° cells — LM4+ offline (WFDE5) vs GIMMS LAI4g",
             fontsize=12)
fig.savefig("figures/lai_trendmap_vs_gimms.png", dpi=140, bbox_inches="tight")

zon = []
for i, la in enumerate(lat1):
    s = rows["mjjas"][2][i]
    if s.sum():
        zon.append([la, np.nanmean(rows["mjjas"][0][i][s]),
                    np.nanmean(rows["mjjas"][1][i][s])])
np.savetxt("lm4/data/lai_trendmap_zonal.csv", np.array(zon), delimiter=",",
           header="lat,lm4_mjjas_trend,gimms_mjjas_trend", comments="", fmt="%.5f")
print("\nwrote figures/lai_trendmap_vs_gimms.png")
