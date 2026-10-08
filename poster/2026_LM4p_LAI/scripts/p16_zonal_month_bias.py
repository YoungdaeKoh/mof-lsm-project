#!/usr/bin/env python3
"""KMS poster: where and when the LAI bias occurs — latitude x month, 1982-2010 climatology.

(a) GIMMS LAI4g zonal mean, (b) LM4+ - GIMMS zonal mean bias, both over common valid 1-deg land cells.
Input: ../data/{lm4p_ctl,gimms}_lai_mon_1982_2020.nc (monthly 1 deg, same files as Fig. 2), years 1982-2010.
output: ../figures/fig_kms_zonal_month_bias.png ; numbers for the text -> ../data/kms_zonal_month_bias.txt
"""
import numpy as np
import netCDF4 as nc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

NY = 29


def read(fn):
    d = nc.Dataset(fn)
    name = [v for v in d.variables if d.variables[v].ndim == 3][0]
    v = np.ma.filled(d.variables[name][: NY * 12].astype("f8"), np.nan)
    return v.reshape(NY, 12, *v.shape[1:]).mean(0), np.asarray(d.variables["lat"][:])


mod, lat = read("../data/lm4p_ctl_lai_mon_1982_2020.nc")
obs, lat2 = read("../data/gimms_lai_mon_1982_2020.nc")
assert np.allclose(lat, lat2) and lat[0] < lat[-1], "lat must be ascending and identical"
ok = np.isfinite(mod).all(0) & np.isfinite(obs).all(0)
# Mask (2026-10-08, after Codex review): a FIXED land-cover mask applied identically to both datasets, not an LAI cutoff
# (GIMMS and LM4+ have different low-LAI floors; an LAI cutoff removed 53 % grassland cells at 0.25).
# BARREN = exclude cells whose MODIS IGBP barren fraction (MCD12C1 2010, grid-verified) is >= BARREN of the land area;
# BARREN=1.01 disables it. MINLAI (GIMMS annual LAI cutoff) kept only as a legacy sensitivity, default off.
import os
BARREN = float(os.environ.get("BARREN", "0.5")); MINLAI = float(os.environ.get("MINLAI", "0"))
ig = np.load("../data/igbp_class_fraction_1deg_2010.npz", allow_pickle=True)
assert np.allclose(ig["lat"], lat), "IGBP grid differs"
fr = np.nan_to_num(ig["fraction"]); bfrac = fr[:, :, 16] / np.maximum(fr[:, :, 1:].sum(2), 1)
nveg0 = ok.sum(); ok &= bfrac < BARREN
if MINLAI > 0:
    ok &= np.where(ok, obs.mean(0), 0) >= MINLAI
print("cells kept (barren fraction < %.2f%s): %d of %d" % (BARREN, ", GIMMS LAI >= %.2f" % MINLAI if MINLAI > 0 else "", ok.sum(), nveg0))
mod = np.where(ok, mod, 0.0); obs = np.where(ok, obs, 0.0)   # invalid cells carry zero weight below
zm = lambda a: np.array([[np.nanmean(a[m, i][ok[i]]) if ok[i].any() else np.nan for m in range(12)] for i in range(lat.size)])
O = zm(obs); B = zm(mod - obs)

# numbers for the text: band means (cos-lat weighted over cells), annual and by season
w = np.cos(np.radians(lat))[:, None] * ok
out = []
for lo, hi, nm in ((-60, -20, "60-20S"), (-20, 20, "20S-20N (tropics)"), (20, 50, "20-50N"), (50, 70, "50-70N"), (-90, 90, "global")):
    b = (lat[:, None] >= lo) & (lat[:, None] < hi) & ok
    ww = w * b
    ann_o = np.sum(obs.mean(0) * ww) / ww.sum(); ann_b = np.sum((mod - obs).mean(0) * ww) / ww.sum()
    son = np.sum((mod - obs)[8:11].mean(0) * ww) / ww.sum(); jja = np.sum((mod - obs)[5:8].mean(0) * ww) / ww.sum()
    out.append("%-18s annual GIMMS %.2f  bias %+.2f (%+.0f %%)  | JJA bias %+.2f  SON bias %+.2f" % (nm, ann_o, ann_b, 100 * ann_b / ann_o, jja, son))
# south-eastern South America (AR6 SES) and the tropics, MJJAS, for the Results 1 text
import regionmask, warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    m3 = regionmask.defined_regions.ar6.land.mask_3D(np.asarray(nc.Dataset("../data/gimms_lai_mon_1982_2020.nc")["lon"][:]), lat)
for ab in ("SES", "NSA", "SAM", "WAF", "CAF", "SEA"):
    r = m3.sel(region=regionmask.defined_regions.ar6.land.map_keys(ab)).values & ok
    ww = np.cos(np.radians(lat))[:, None] * r
    mo = np.sum(obs[4:9].mean(0) * ww) / ww.sum(); mm = np.sum(mod[4:9].mean(0) * ww) / ww.sum()
    out.append("AR6 %-4s MJJAS GIMMS %.2f  LM4+ %.2f  bias %+.2f (%+.0f %%)" % (ab, mo, mm, mm - mo, 100 * (mm - mo) / mo))
open("../data/kms_zonal_month_bias.txt", "w").write("\n".join(out) + "\n"); print("\n".join(out))

mon = np.arange(1, 13)
fig, axs = plt.subplots(1, 2, figsize=(11, 5.2), sharey=True, gridspec_kw={"wspace": 0.08})
c0 = axs[0].contourf(mon, lat, O, levels=np.arange(0, 5.01, 0.5), cmap="YlGn", extend="max")
from matplotlib.colors import BoundaryNorm
LEV = [-3, -2, -1.5, -1, -0.5, -0.25, 0.25, 0.5, 1, 1.5, 2, 3]          # symmetric, same as Fig. 1(c); white = |bias| < 0.25
cm = plt.get_cmap("BrBG", len(LEV) + 1)
c1 = axs[1].contourf(mon, lat, B, levels=LEV, cmap=cm, norm=BoundaryNorm(LEV, cm.N, extend="both"), extend="both")
for ax, c, t, lab in ((axs[0], c0, "(a) GIMMS LAI", "LAI (m$^2$ m$^{-2}$)"), (axs[1], c1, "(b) LM4+ $-$ GIMMS", "LAI difference")):
    ax.set_title(t, loc="left", fontsize=12); ax.set_xticks(mon); ax.set_xticklabels(list("JFMAMJJASOND"))
    ax.set_ylim(-60, 80); ax.set_yticks(range(-60, 81, 20)); ax.grid(alpha=0.3, ls=":")
    for y0 in (20, 50):
        ax.axhline(y0, color="0.3", lw=0.6, ls="--")
    cb = fig.colorbar(c, ax=ax, orientation="horizontal", pad=0.1, shrink=0.9, label=lab)
    if c is c1:
        cb.set_ticks([-3, -2, -1, -0.5, 0.5, 1, 2, 3])
axs[0].set_yticklabels(["60S", "40S", "20S", "EQ", "20N", "40N", "60N", "80N"]); axs[0].set_ylabel("Latitude")
fig.savefig("../figures/fig_kms_zonal_month_bias.png", dpi=200, bbox_inches="tight")
print("wrote ../figures/fig_kms_zonal_month_bias.png")
