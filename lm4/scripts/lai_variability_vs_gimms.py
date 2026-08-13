"""Interannual variability of MJJAS LAI, LM4+ vs GIMMS LAI4g, 1990-2010.

The window matches the trend figure: 1982-89 is spin-up drift, and removing a
straight line from it does not make it climate variability -- an adjustment is
not a trend.  The finished chain leaves twenty-one clean years, against the
fifteen drift-included years this figure used before.

The mean map says how much leaf area there is and the trend map says how it
drifts; neither says how much it swings from year to year.  That turned out to
be a first-order error in its own right: the model's detrended interannual
standard deviation is 3.6x the observed, so LM4 vegetation wobbles by 11.4 % of
its own mean each year where the observations wobble by 4.7 %.  (The fifteen-year
version of this figure put the ratio at 4.5x; part of that was the drift years
being counted as spread even after a straight line was removed.)

The trend is still removed within the window, so that the residual greening is
not counted as variability.

Row 1 is the absolute spread, row 2 the coefficient of variation (spread as a
percentage of the cell mean), the same absolute/normalised pairing the trend
figure uses.  Cells with a mean below 0.5 are dropped from row 2.

Caveat worth carrying: satellite LAI is composited and smoothed, so part of the
gap may be damped observed variability rather than excess model variability.
Cross-checking against MODIS or GLASS would settle it.

Inputs : lm4/data/lm4_lai_1982_2010.npz, lm4/data/gimms_1deg_1982_2010.npz
Output : figures/lai_variability_vs_gimms.png, lm4/data/lai_variability_zonal.csv
"""
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

YEARS = np.arange(1990, 2011)
NLAT, NLON = 180, 360
lat1 = 89.5 - np.arange(NLAT)
lon1 = -179.5 + np.arange(NLON)

z = np.load("lm4/data/lm4_lai_1982_2010.npz")
g = np.load("lm4/data/gimms_1deg_1982_2010.npz")
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


t = YEARS - YEARS.mean()
den = (t ** 2).sum()


def detrended_sd(stack):
    """Standard deviation about the fitted line, so drift is not counted twice."""
    an = stack - stack.mean(axis=0)
    slope = (an * t[:, None, None]).sum(axis=0) / den
    res = an - slope[None, :, :] * t[:, None, None]
    return res.std(axis=0, ddof=2)


ms = np.stack([bin_model(z["mjjas_%d" % y]) for y in YEARS])
gs = np.stack([g["mjjas_%d" % y] for y in YEARS])
common = np.all(np.isfinite(ms), axis=0) & np.all(np.isfinite(gs), axis=0)
W = np.cos(np.deg2rad(lat1))[:, None] * np.ones((1, NLON))

sm = np.where(common, detrended_sd(np.where(common, ms, 0.0)), np.nan)
sg = np.where(common, detrended_sd(np.where(common, gs, 0.0)), np.nan)
mbar = np.where(common, ms.mean(axis=0), np.nan)
gbar = np.where(common, gs.mean(axis=0), np.nan)

veg = common & (mbar > 0.5) & (gbar > 0.5)
with np.errstate(invalid="ignore", divide="ignore"):
    cm = np.where(veg, sm / mbar * 100.0, np.nan)
    cg = np.where(veg, sg / gbar * 100.0, np.nan)

ROWS = [
    ("absolute", "m$^2$/m$^2$", sm, sg, common,
     np.array([0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0]),
     np.array([-0.6, -0.4, -0.25, -0.15, -0.05, 0.05, 0.15, 0.25, 0.4, 0.6])),
    ("coefficient of variation", "% of the cell mean", cm, cg, veg,
     np.array([0, 1, 2, 3, 5, 8, 12, 18, 25, 35]),
     np.array([-20, -12, -8, -5, -2, 2, 5, 8, 12, 20])),
]

for name, unit, a, b, sel, _, _ in ROWS:
    w = np.where(sel, W, 0.0)
    am = np.nansum(np.where(sel, a, 0) * w) / w.sum()
    ag = np.nansum(np.where(sel, b, 0) * w) / w.sum()
    print("\n=== MJJAS interannual variability, %s  (%d cells) ===" % (name, sel.sum()))
    print("  area-weighted   LM4 %.4f   GIMMS %.4f   ratio %.2f  [%s]"
          % (am, ag, am / ag, unit))
    print("  cells where the model is more variable: %.1f %%"
          % (100 * np.nanmean(a[sel] > b[sel])))
    print("  zonal mean")
    print("    band          LM4    GIMMS    ratio")
    for a0, a1 in ((60, 85), (30, 60), (0, 30), (-30, 0), (-60, -30)):
        s = sel & (lat1[:, None] >= a0) & (lat1[:, None] < a1)
        if s.sum():
            ww = np.where(s, W, 0.0)
            vm = np.nansum(np.where(s, a, 0) * ww) / ww.sum()
            vg = np.nansum(np.where(s, b, 0) * ww) / ww.sum()
            print("    %4d..%-4d %8.3f %8.3f %8.2f" % (a0, a1, vm, vg, vm / vg))

# ------------------------------------------------------------------ figure ---
proj = ccrs.PlateCarree()
fig, axes = plt.subplots(2, 3, figsize=(19, 9.4), subplot_kw={"projection": proj},
                         constrained_layout=True)
titles = ["GIMMS LAI4g (obs)", "LM4+ (model)", "LM4+ − GIMMS"]
for r, (name, unit, a, b, sel, lv, lvd) in enumerate(ROWS):
    ims = []
    for c, (fld, levels, cmap) in enumerate(((b, lv, "YlOrRd"), (a, lv, "YlOrRd"),
                                             (a - b, lvd, "RdBu_r"))):
        ax = axes[r, c]
        ax.set_extent([-180, 180, -58, 84], crs=proj)
        ax.add_feature(cfeature.COASTLINE, lw=0.4)
        ims.append(ax.contourf(lon1, lat1, np.where(sel, fld, np.nan),
                               levels=levels, cmap=cmap, extend="max" if c < 2 else "both",
                               transform=proj))
        ax.set_title("%s   %s" % (titles[c], "sd" if r == 0 else "sd / mean"),
                     fontsize=15)
        gl = ax.gridlines(draw_labels=True, lw=0.3, alpha=0.4)
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {"size": 11}
        gl.ylabel_style = {"size": 11}
    cb = fig.colorbar(ims[0], ax=[axes[r, 0], axes[r, 1]], orientation="horizontal",
                      ticks=lv, shrink=0.7, pad=0.02, aspect=45)
    cb.ax.tick_params(labelsize=11)
    cb.set_label("interannual sd [%s]" % unit, fontsize=13)
    cb2 = fig.colorbar(ims[2], ax=axes[r, 2], orientation="horizontal",
                       ticks=lvd, shrink=0.9, pad=0.02, aspect=25)
    cb2.ax.tick_params(labelsize=11)
    cb2.set_label("difference [%s]" % unit, fontsize=13)

fig.suptitle("MJJAS LAI interannual variability %d–%d (trend removed, drift years "
             "1982–89 excluded) — LM4+ offline (WFDE5) vs GIMMS LAI4g\n"
             % (YEARS[0], YEARS[-1]) +
             "top: standard deviation;  bottom: the same as a percentage of each "
             "cell's mean", fontsize=17)
fig.savefig("figures/lai_variability_vs_gimms.png", dpi=140, bbox_inches="tight")

zon = []
for i, la in enumerate(lat1):
    s = common[i]
    if s.sum():
        zon.append([la, np.nanmean(sm[i][s]), np.nanmean(sg[i][s])])
np.savetxt("lm4/data/lai_variability_zonal.csv", np.array(zon), delimiter=",",
           header="lat,lm4_mjjas_sd,gimms_mjjas_sd", comments="", fmt="%.5f")
print("\nwrote figures/lai_variability_vs_gimms.png")
