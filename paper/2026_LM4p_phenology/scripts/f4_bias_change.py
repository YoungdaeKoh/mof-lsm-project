#!/usr/bin/env python3
"""Fig. 4: how much of the SOS / EOS bias the modified rules remove (CTRL vs EXP against three satellite LAI products).

(a, b) SOS bias of CTRL and EXP, (c, d) EOS bias of CTRL and EXP: model - mean of GIMMS-cons / GIMMS-AVHRR / GLASS,
       cell by cell, days (+ = model later)
(e, f) SOS and EOS bias per latitude band, CTRL and EXP side by side; error bar = mean observational spread
Same method as Fig. 1 (f1_ctrl_bias_regions.py): monthly means at mid-month, linear interpolation to days, 50 %
amplitude crossings on the mean monthly curve over YEARS of each cell; cells with GIMMS amplitude >= 0.5 (observed
season), north of 20N, finite in all five fields; cells with CTRL amplitude < 0.3 (no modelled vegetation) left out.
Set CASE below: "2010" = 1-yr phentest pair (CTRL = phentest base, same set-up as EXP except the rules);
the 15-yr pair is filled in when the FULL run exists.
output: ../figures/f4_bias_change.png, ../data/f4_bias_change.txt
"""
import warnings
import numpy as np
import netCDF4 as nc
import regionmask
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature

P = "../../../poster/2026_LM4p_LAI/data/"
CASES = {"2010": dict(A=2010, B=2010, CTRL=(P + "base.lai.2010-2010.1deg.nc", 2010), EXP=(P + "dayl.lai.2010-2010.1deg.nc", 2010),
                      label="DL13/12 (autumn day-length rule)")}
CASE = "2010"
C = CASES[CASE]; A, B = C["A"], C["B"]; NY = B - A + 1
FILES = {"GIMMS": (P + "gimms_lai_mon_1982_2020.nc", 1982), "AVHRR": (P + "gimms_solely_lai_mon_1982_2015.nc", 1982),
         "GLASS": (P + "glass_lai_modis_monthly_1deg_2001_2020.nc", 2001), "CTRL": C["CTRL"], "EXP": C["EXP"]}
OBS = ("GIMMS", "AVHRR", "GLASS")
BANDS = [("20–40N", 20, 40), ("40–50N", 40, 50), ("50–60N", 50, 60), ("60–70N", 60, 70)]
MID = np.array([15.5, 45.0, 74.5, 105.0, 135.5, 166.0, 196.5, 227.5, 258.0, 288.5, 319.0, 349.5])
DOY = np.arange(1, 366)


def read(fn, y0):
    with nc.Dataset(fn) as d:
        name = [v for v in d.variables if d.variables[v].ndim == 3][0]
        assert np.allclose(d["lat"][:], -89.5 + np.arange(180)) and np.allclose(d["lon"][:], -179.5 + np.arange(360))
        v = np.ma.filled(d.variables[name][(A - y0) * 12:(B - y0 + 1) * 12].astype("f8"), np.nan)
    v[np.abs(v) > 100] = np.nan
    return v


def sos_eos(c):
    lo, hi = c.min(), c.max(); thr = lo + 0.5 * (hi - lo); ip = int(c.argmax())
    up = np.where((c[:-1] < thr) & (c[1:] >= thr))[0]; dn = np.where((c[:-1] >= thr) & (c[1:] < thr))[0]
    up = up[up < ip]; dn = dn[dn >= ip]; s = e = np.nan
    if up.size:
        i = up[-1]; s = DOY[i] + (thr - c[i]) / (c[i + 1] - c[i])
    if dn.size:
        i = dn[0]; e = DOY[i] + (c[i] - thr) / (c[i] - c[i + 1])
    return s, e


data = {k: read(*FILES[k]) for k in FILES}
ok = np.all([np.isfinite(v).all(0) for v in data.values()], 0)
lat = -89.5 + np.arange(180); lon = -179.5 + np.arange(360)
W = np.cos(np.radians(lat))[:, None] * np.ones((1, 360))
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    land = regionmask.defined_regions.ar6.land.mask_3D(lon, lat).values.any(0)
clim = {k: v.reshape(NY, 12, 180, 360).mean(0) for k, v in data.items()}
noveg = (clim["CTRL"].max(0) - clim["CTRL"].min(0)) < 0.3
cells = ok & land & (lat >= 20)[:, None] & ((clim["GIMMS"].max(0) - clim["GIMMS"].min(0)) >= 0.5) & ~noveg
S = {k: np.full((180, 360), np.nan) for k in data}; E = {k: np.full((180, 360), np.nan) for k in data}
for i, j in zip(*np.where(cells)):
    for k in data:
        m = clim[k][:, i, j]
        S[k][i, j], E[k][i, j] = sos_eos(np.interp(DOY, np.r_[MID[-1] - 365, MID, MID[0] + 365], np.r_[m[-1], m, m[0]]))
obs = {"SOS": np.mean([S[p] for p in OBS], 0), "EOS": np.mean([E[p] for p in OBS], 0)}
spr = {"SOS": np.ptp([S[p] for p in OBS], 0), "EOS": np.ptp([E[p] for p in OBS], 0)}
bias = {(r, key): (S if key == "SOS" else E)[r] - obs[key] for r in ("CTRL", "EXP") for key in ("SOS", "EOS")}

out = ["SOS/EOS bias, CTRL vs EXP = %s, %d-%d, per cell (GIMMS amplitude >= 0.5, CTRL amplitude >= 0.3), cos-lat mean, days" % (C["label"], A, B),
       "%-8s %5s | %7s %7s %7s %6s | %7s %7s %7s %6s" % ("band", "cells", "SOS_C", "SOS_X", "change", "sprd", "EOS_C", "EOS_X", "change", "sprd")]
tab = {}
for nm, a, b in BANDS + [("50–70N", 50, 70)]:
    mk = cells & ((lat >= a) & (lat < b))[:, None]
    row = []
    for key in ("SOS", "EOS"):
        v = mk & np.isfinite(bias[("CTRL", key)]) & np.isfinite(bias[("EXP", key)]); w = W * v
        mc, mx = [np.nansum(bias[(r, key)] * w) / w.sum() for r in ("CTRL", "EXP")]
        row += [mc, mx, mx - mc, np.nansum(spr[key] * w) / w.sum()]
    tab[nm] = row
    out.append("%-8s %5d | %+7.1f %+7.1f %+7.1f %6.1f | %+7.1f %+7.1f %+7.1f %6.1f" % (nm, mk.sum(), *row))

fig = plt.figure(figsize=(13, 7.4))
gs = fig.add_gridspec(3, 2, height_ratios=(0.62, 0.62, 1.15), hspace=0.22, wspace=0.06)
proj = ccrs.PlateCarree(central_longitude=180)
lev = np.arange(-60, 61, 10); norm = BoundaryNorm(lev, 256, extend="both")
for n, (key, run) in enumerate([("SOS", "CTRL"), ("SOS", "EXP"), ("EOS", "CTRL"), ("EOS", "EXP")]):
    ax = fig.add_subplot(gs[n // 2, n % 2], projection=proj)
    ax.set_extent([-180, 180, 20, 80], crs=proj)
    im = ax.pcolormesh(lon, lat, np.ma.masked_invalid(bias[(run, key)]), cmap="RdBu_r", norm=norm,
                       transform=ccrs.PlateCarree(), shading="auto")
    ax.coastlines(lw=0.4, color="0.3"); ax.add_feature(cfeature.LAND, facecolor="0.93", zorder=0)
    gl = ax.gridlines(draw_labels=True, lw=0.3, color="0.6", ls=":", xlocs=range(-180, 181, 60), ylocs=range(20, 81, 20))
    gl.top_labels = False; gl.right_labels = False; gl.xlabel_style = {"size": 7.5}; gl.ylabel_style = {"size": 7.5}
    if n % 2:
        gl.left_labels = False
    if n < 2:
        gl.bottom_labels = False
    ax.text(0.01, 0.04, "50–70N %+.0f d" % tab["50–70N"][(0 if run == "CTRL" else 1) + (0 if key == "SOS" else 4)], transform=ax.transAxes,
            fontsize=8.5, bbox=dict(fc="white", ec="none", alpha=0.85))
    ax.set_title("(%s) %s bias, %s" % ("abcd"[n], key, "LM4.1 CTRL" if run == "CTRL" else "EXP"), loc="left", fontsize=10)
maps = [a for a in fig.axes]
fig.canvas.draw()
p0, p1 = maps[1].get_position(), maps[3].get_position()
cax = fig.add_axes([p0.x1 + 0.01, p1.y0, 0.01, p0.y1 - p1.y0])
cb = fig.colorbar(im, cax=cax); cb.set_label("model − observed mean (days)", fontsize=8.5); cb.ax.tick_params(labelsize=8)

names = [b[0] for b in BANDS]; x = np.arange(len(names))
for n, (key, k0, col) in enumerate((("SOS", 0, "#2c7fb8"), ("EOS", 4, "#d95f0e"))):
    ax = fig.add_subplot(gs[2, n])
    c = np.array([tab[nm][k0] for nm in names]); e = np.array([tab[nm][k0 + 1] for nm in names]); sp = np.array([tab[nm][k0 + 3] for nm in names])
    ax.bar(x - 0.19, c, 0.36, color="0.6", label="LM4.1 CTRL")
    ax.bar(x + 0.19, e, 0.36, color=col, label="EXP")
    ax.errorbar(x + 0.19, e, yerr=sp / 2, fmt="none", ecolor="k", elinewidth=1, capsize=3, label="observational spread")
    for xi, ci, ei, sp_i in zip(x, c, e, sp):
        ax.text(xi - 0.19, max(ci, 0) + 1.5, "%+.0f" % ci, ha="center", fontsize=8, color="0.35")
        ax.text(xi + 0.19, max(ei, 0) + sp_i / 2 + 1.5, "%+.0f" % ei, ha="center", fontsize=8, color=col, weight="bold")
    ax.axhline(0, color="k", lw=0.8); ax.set_xticks(x); ax.set_xticklabels(names, fontsize=8.5)
    ax.set_ylim(-35, 60); ax.grid(axis="y", alpha=0.25); ax.tick_params(axis="y", labelsize=8.5)
    ax.set_title("(%s) %s bias by latitude band (%d%s)" % ("ef"[n], key, A, "" if A == B else "–%d" % B), loc="left", fontsize=10)
    if n == 0:
        ax.set_ylabel("Bias (days, + = model later)", fontsize=9)
    ax.legend(fontsize=7.5, frameon=False, loc="upper left")
fig.text(0.01, 0.005, "EXP = %s" % C["label"], fontsize=8, color="0.35")
fig.savefig("../figures/f4_bias_change.png", dpi=200, bbox_inches="tight")
open("../data/f4_bias_change.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
