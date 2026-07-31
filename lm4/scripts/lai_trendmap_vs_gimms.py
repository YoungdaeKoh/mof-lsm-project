"""Per-cell MJJAS LAI trends, LM4+ vs GIMMS LAI4g, 1982-1996.

The absolute trend is not a fair comparison on its own: the model's mean LAI is
1.42x the observed, so identical fractional growth would already show up as a
1.42x larger slope.  Subtracting the period mean does not fix that -- a
least-squares slope is unchanged by adding or subtracting a constant, and
trend() already fits anomalies.  Removing the size effect means dividing, not
subtracting, so the second row divides each cell's trend by that same cell's
own mean and reports % per decade.  (Equivalently: build the anomaly as a
percentage of the cell mean and fit the trend to that; the mean is a constant,
so it commutes with the fit.)

Cells with a mean below 0.5 are dropped from the normalised row -- dividing by a
near-zero mean explodes, and a desert cell's percentage change means nothing.

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
    """Least-squares slope per cell, per decade (already an anomaly fit)."""
    t = YEARS - YEARS.mean()
    an = stack - stack.mean(axis=0)
    return (an * t[:, None, None]).sum(axis=0) / (t ** 2).sum() * 10.0


ms = np.stack([bin_model(z["mjjas_%d" % y]) for y in YEARS])
gs = np.stack([g["mjjas_%d" % y] for y in YEARS])
common = np.all(np.isfinite(ms), axis=0) & np.all(np.isfinite(gs), axis=0)
W = np.cos(np.deg2rad(lat1))[:, None] * np.ones((1, NLON))

tm = np.where(common, trend(np.where(common, ms, 0.0)), np.nan)
tg = np.where(common, trend(np.where(common, gs, 0.0)), np.nan)
mbar = np.where(common, ms.mean(axis=0), np.nan)
gbar = np.where(common, gs.mean(axis=0), np.nan)

veg = common & (mbar > 0.5) & (gbar > 0.5)
with np.errstate(invalid="ignore", divide="ignore"):
    rm = np.where(veg, tm / mbar * 100.0, np.nan)
    rg = np.where(veg, tg / gbar * 100.0, np.nan)

ROWS = [
    ("absolute", "m$^2$/m$^2$ per decade", tm, tg, common,
     np.array([-0.6, -0.4, -0.25, -0.15, -0.05, 0.05, 0.15, 0.25, 0.4, 0.6])),
    ("normalised by the cell mean", "% per decade", rm, rg, veg,
     np.array([-12, -8, -5, -3, -1, 1, 3, 5, 8, 12])),
]

for name, unit, a, b, sel, _ in ROWS:
    w = np.where(sel, W, 0.0)
    am = np.nansum(np.where(sel, a, 0) * w) / w.sum()
    ag = np.nansum(np.where(sel, b, 0) * w) / w.sum()
    print("\n=== MJJAS trend, %s  (%d cells) ===" % (name, sel.sum()))
    print("  area-weighted mean   LM4 %+.4f   GIMMS %+.4f   ratio %.2f"
          % (am, ag, am / ag if ag else np.nan))
    print("  cells with positive trend  LM4 %5.1f %%   GIMMS %5.1f %%"
          % (100 * np.nanmean(a[sel] > 0), 100 * np.nanmean(b[sel] > 0)))
    print("  |trend| p98                LM4 %8.3f  GIMMS %8.3f"
          % (np.nanpercentile(np.abs(a[sel]), 98),
             np.nanpercentile(np.abs(b[sel]), 98)))
    print("  zonal mean")
    print("    band          LM4    GIMMS     diff")
    for a0, a1 in ((60, 85), (30, 60), (0, 30), (-30, 0), (-60, -30)):
        s = sel & (lat1[:, None] >= a0) & (lat1[:, None] < a1)
        if s.sum():
            ww = np.where(s, W, 0.0)
            vm = np.nansum(np.where(s, a, 0) * ww) / ww.sum()
            vg = np.nansum(np.where(s, b, 0) * ww) / ww.sum()
            print("    %4d..%-4d %+8.3f %+8.3f %+8.3f" % (a0, a1, vm, vg, vm - vg))

# ------------------------------------------------------------------ figure ---
proj = ccrs.PlateCarree()
fig, axes = plt.subplots(2, 3, figsize=(19, 9.4), subplot_kw={"projection": proj},
                         constrained_layout=True)
titles = ["GIMMS LAI4g (obs)", "LM4+ (model)", "LM4+ − GIMMS"]
for r, (name, unit, a, b, sel, lv) in enumerate(ROWS):
    ims = []
    # observation first: it is the reference the model is judged against
    for c, (fld, cmap) in enumerate(((b, "BrBG"), (a, "BrBG"), (a - b, "RdBu_r"))):
        ax = axes[r, c]
        ax.set_extent([-180, 180, -58, 84], crs=proj)
        ax.add_feature(cfeature.COASTLINE, lw=0.4)
        ims.append(ax.contourf(lon1, lat1, np.where(sel, fld, np.nan), levels=lv,
                               cmap=cmap, extend="both", transform=proj))
        ax.set_title("%s   %s" % (titles[c], "absolute" if r == 0 else "normalised"),
                     fontsize=15)
        gl = ax.gridlines(draw_labels=True, lw=0.3, alpha=0.4)
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {"size": 11}
        gl.ylabel_style = {"size": 11}
    cb = fig.colorbar(ims[0], ax=[axes[r, 0], axes[r, 1]], orientation="horizontal",
                      ticks=lv, shrink=0.7, pad=0.02, aspect=45)
    cb.ax.tick_params(labelsize=11)
    cb.set_label("MJJAS LAI trend [%s]" % unit, fontsize=13)
    cb2 = fig.colorbar(ims[2], ax=axes[r, 2], orientation="horizontal",
                       ticks=lv, shrink=0.9, pad=0.02, aspect=25)
    cb2.ax.tick_params(labelsize=11)
    cb2.set_label("difference [%s]" % unit, fontsize=13)

fig.suptitle("MJJAS LAI trend 1982–1996 — LM4+ offline (WFDE5) vs GIMMS LAI4g, common 1° cells\n"
             "top: absolute;  bottom: each cell divided by its own mean, so the "
             "model's larger LAI cannot inflate the trend", fontsize=17)
fig.savefig("figures/lai_trendmap_vs_gimms.png", dpi=140, bbox_inches="tight")

zon = []
for i, la in enumerate(lat1):
    s = common[i]
    if s.sum():
        zon.append([la, np.nanmean(tm[i][s]), np.nanmean(tg[i][s])])
np.savetxt("lm4/data/lai_trendmap_zonal.csv", np.array(zon), delimiter=",",
           header="lat,lm4_mjjas_trend,gimms_mjjas_trend", comments="", fmt="%.5f")
print("\nwrote figures/lai_trendmap_vs_gimms.png")
