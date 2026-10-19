#!/usr/bin/env python3
"""Fig. 1: the CTRL phenology bias against three satellite LAI products, 2001-2015.

(a) GIMMS LAI4g May-Sep (MJJAS) mean 2001-2015, 20-80N
(b) CTRL - GIMMS MJJAS mean LAI (cells valid in all products)
(c) normalised LAI seasonal cycle of the boreal land (50-70N; each curve scaled by its own 15-yr mean min/max, so
    winter floors drop out): observed range (min-max over GIMMS-cons, GIMMS-AVHRR, GLASS) shaded, CTRL in red
(d) SOS and EOS bias of CTRL per latitude band 20-40, 40-50, 50-60, 60-70N, computed CELL BY CELL on the 15-yr mean
    monthly curve of each product (cells with GIMMS amplitude >= 0.5 m2 m-2, i.e. an observed season; no criterion on
    the model). Bar = cos-lat mean of (CTRL - mean of the three products); error bar = cos-lat mean of the product
    spread (max-min). Cells where CTRL has no 50 % crossing before Dec 31 (no modelled leaf-off) are excluded from the
    mean and reported as a percentage above the bar. The tropics are left out (no single temperature-driven season).
Method = poster p24 (cos-lat mean over cells valid in every product and month, monthly -> daily interpolation,
per-year 50 % amplitude crossings, mean over years). AR6-region version of (d): ../data/f1_sos_eos_bias.txt (SI).
input : ../../../poster/2026_LM4p_LAI/data/{lm4p_ctl_lai_mon_1982_2020,gimms_lai_mon_1982_2020,
        gimms_solely_lai_mon_1982_2015,glass_lai_modis_monthly_1deg_2001_2020}.nc
output: ../figures/f1_ctrl_bias_regions.png, ../data/f1_sos_eos_bias.txt
"""
import warnings
import numpy as np
import netCDF4 as nc
import regionmask
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

P = "../../../poster/2026_LM4p_LAI/data/"
FILES = {"GIMMS": (P + "gimms_lai_mon_1982_2020.nc", 1982), "AVHRR": (P + "gimms_solely_lai_mon_1982_2015.nc", 1982),
         "GLASS": (P + "glass_lai_modis_monthly_1deg_2001_2020.nc", 2001), "CTRL": (P + "lm4p_ctl_lai_mon_1982_2020.nc", 1982)}
OBS = ("GIMMS", "AVHRR", "GLASS")
A, B = 2001, 2015
BANDS = [("20–40N", 20, 40), ("40–50N", 40, 50), ("50–60N", 50, 60), ("60–70N", 60, 70)]
AR6 = ["NEU", "RFE", "NWN", "ESB", "WSB", "NEN", "RAR"]   # SI table only
MID = np.array([15.5, 45.0, 74.5, 105.0, 135.5, 166.0, 196.5, 227.5, 258.0, 288.5, 319.0, 349.5])
DOY = np.arange(1, 366)
NY = B - A + 1


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
ar6 = regionmask.defined_regions.ar6.land
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    m3 = ar6.mask_3D(lon, lat)
land = m3.values.any(0)
REG = {nm: land & ((lat >= a) & (lat < b))[:, None] for nm, a, b in BANDS}
REG["boreal"] = land & ((lat >= 50) & (lat <= 70))[:, None]
REG.update({ab: m3.sel(region=ar6.map_keys(ab)).values.astype(bool) for ab in AR6})


def region(mask):
    """per product: mean normalised daily curve (over years) and yearly (SOS, EOS)."""
    w = W * (ok & mask)
    res = {}
    for k, v in data.items():
        ts = np.array([np.nansum(v[t] * w) / w.sum() for t in range(NY * 12)]).reshape(NY, 12)
        cur, st = [], []
        for y in range(NY):
            pd = ts[y - 1, 11] if y > 0 else ts[y, 11]; nj = ts[y + 1, 0] if y < NY - 1 else ts[y, 0]
            c = np.interp(DOY, np.r_[MID[-1] - 365, MID, MID[0] + 365], np.r_[pd, ts[y], nj])
            cur.append(c); st.append(sos_eos(c))
        cur = np.array(cur).mean(0)
        res[k] = ((cur - cur.min()) / (cur.max() - cur.min()), np.array(st))
    return res, int((w > 0).sum())


def bias_of(res):
    out = {}
    for j, key in enumerate(("SOS", "EOS")):
        o = np.array([np.nanmean(res[p][1][:, j]) for p in OBS]); m = np.nanmean(res["CTRL"][1][:, j])
        out[key] = (o, m, m - o.mean(), o.max() - o.min())
    return out


out = ["CTRL SOS/EOS bias vs three satellite LAI products, %d-%d, 50 %% amplitude, days (+ = model later)" % (A, B),
       "%-8s %5s | %6s %6s %6s %6s | %6s %6s | %6s %6s %6s %6s | %6s %6s" % ("region", "cells", "sosG", "sosA", "sosGL", "sosM", "dSOS", "sprd", "eosG", "eosA", "eosGL", "eosM", "dEOS", "sprd")]
bias = {}
for ab in ["boreal"] + [b[0] for b in BANDS] + AR6:
    res, n = region(REG[ab])
    bias[ab] = bias_of(res)
    if ab == "boreal":
        boreal_res, boreal_n = res, n
    r = bias[ab]
    out.append("%-8s %5d | %6.1f %6.1f %6.1f %6.1f | %+6.1f %6.1f | %6.1f %6.1f %6.1f %6.1f | %+6.1f %6.1f" % (
        ab, n, *r["SOS"][0], r["SOS"][1], r["SOS"][2], r["SOS"][3], *r["EOS"][0], r["EOS"][1], r["EOS"][2], r["EOS"][3]))

# ---- per-cell SOS/EOS on the 15-yr mean curve (for panel d)
AMP = 0.5
clim = {k: v.reshape(NY, 12, 180, 360).mean(0) for k, v in data.items()}
has_season = ok & ((clim["GIMMS"].max(0) - clim["GIMMS"].min(0)) >= AMP)
cs = {k: np.full((180, 360), np.nan) for k in data}; ce = {k: np.full((180, 360), np.nan) for k in data}
for i, j in zip(*np.where(has_season)):
    for k in data:
        mth = clim[k][:, i, j]
        c = np.interp(DOY, np.r_[MID[-1] - 365, MID, MID[0] + 365], np.r_[mth[-1], mth, mth[0]])
        cs[k][i, j], ce[k][i, j] = sos_eos(c)
obs_s = np.mean([cs[p] for p in OBS], 0); obs_e = np.mean([ce[p] for p in OBS], 0)
spr_s = np.max([cs[p] for p in OBS], 0) - np.min([cs[p] for p in OBS], 0)
spr_e = np.max([ce[p] for p in OBS], 0) - np.min([ce[p] for p in OBS], 0)
cellbias = {}
out += ["", "per-cell version (GIMMS amplitude >= %.1f): cos-lat mean bias, mean product spread, %% cells with no CTRL crossing" % AMP,
        "%-8s %5s | %6s %6s %6s | %6s %6s %6s" % ("band", "cells", "dSOS", "sprd", "noSOS%", "dEOS", "sprd", "noEOS%")]
for nm, a, b in BANDS + [("boreal", 50, 70)]:
    mk = has_season & land & ((lat >= a) & (lat < b))[:, None]
    row = []
    for cm, om, sp in ((cs["CTRL"], obs_s, spr_s), (ce["CTRL"], obs_e, spr_e)):
        v = mk & np.isfinite(cm) & np.isfinite(om)
        w = W * v
        row += [np.nansum((cm - om) * w) / w.sum(), np.nansum(sp * w) / w.sum(), 100 * (mk & np.isfinite(om) & ~np.isfinite(cm)).sum() / max((mk & np.isfinite(om)).sum(), 1)]
    cellbias[nm] = row
    out.append("%-8s %5d | %+6.1f %6.1f %6.1f | %+6.1f %6.1f %6.1f" % (nm, mk.sum(), *row))

# ---- figure
fig = plt.figure(figsize=(13, 8.8))
gs = fig.add_gridspec(2, 2, height_ratios=(1, 1.05), hspace=0.12, wspace=0.08)
proj = ccrs.PlateCarree(central_longitude=180)
axa = fig.add_subplot(gs[0, 0], projection=proj); axb = fig.add_subplot(gs[0, 1], projection=proj)
axc = fig.add_subplot(gs[1, 0]); axd = fig.add_subplot(gs[1, 1])

g = data["GIMMS"].reshape(NY, 12, 180, 360)[:, 4:9].mean((0, 1))
m = data["CTRL"].reshape(NY, 12, 180, 360)[:, 4:9].mean((0, 1))
mb = np.where(ok, m - g, np.nan)
for ax, z, cmap, lo, hi, lab, title in ((axa, g, "YlGn", 0, 5, "LAI (m$^2$ m$^{-2}$)", "(a) Observed LAI, May–Sep mean %d–%d (GIMMS LAI4g)" % (A, B)),
                                        (axb, mb, "RdBu_r", -2.5, 2.5, "ΔLAI (m$^2$ m$^{-2}$)", "(b) CTRL − observed, May–Sep mean")):
    ax.set_extent([-180, 180, -10, 80], crs=proj)   # full width, Pacific-centred
    im = ax.pcolormesh(lon, lat, np.ma.masked_invalid(z), cmap=cmap, vmin=lo, vmax=hi, transform=ccrs.PlateCarree(), shading="auto")
    ax.coastlines(lw=0.4, color="0.3"); ax.add_feature(cfeature.OCEAN, facecolor="#eef3f7", zorder=0)
    gl = ax.gridlines(draw_labels=True, lw=0.3, color="0.6", ls=":", xlocs=range(-180, 181, 60), ylocs=range(0, 81, 20))
    gl.top_labels = False; gl.right_labels = False; gl.xlabel_style = {"size": 7.5}; gl.ylabel_style = {"size": 7.5}
    if ax is axb:
        gl.left_labels = False
    cb = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.06, shrink=0.6, aspect=35); cb.set_label(lab, fontsize=8); cb.ax.tick_params(labelsize=7.5)
    ax.set_title(title, loc="left", fontsize=10)
wb = W * (ok & REG["boreal"])
axb.text(0.01, 0.03, "50–70N land mean: %+.2f (%+.0f %%)" % (np.nansum(mb * wb) / wb.sum(), 100 * np.nansum(m * wb) / np.nansum(g * wb) - 100),
         transform=axb.transAxes, fontsize=8, bbox=dict(fc="white", ec="none", alpha=0.85))

# (c) boreal seasonal cycle
O = np.array([boreal_res[p][0] for p in OBS])
axc.fill_between(DOY, O.min(0), O.max(0), color="0.55", alpha=0.45, lw=0, label="Observed range (GIMMS, AVHRR, GLASS)")
axc.plot(DOY, O.mean(0), color="0.2", lw=1.3, label="Observed mean")
axc.plot(DOY, boreal_res["CTRL"][0], color="tab:red", lw=2.4, label="CTRL")
axc.axhline(0.5, color="0.6", lw=0.7, ls=":")
bb = bias["boreal"]
for key, j, col in (("SOS", 0, "#2c7fb8"), ("EOS", 1, "#d95f0e")):
    o = np.mean([np.nanmean(boreal_res[p][1][:, j]) for p in OBS]); mm = np.nanmean(boreal_res["CTRL"][1][:, j])
    axc.annotate("", xy=(mm, 0.5), xytext=(o, 0.5), arrowprops=dict(arrowstyle="->", color=col, lw=2))
    axc.text((o + mm) / 2, 0.54, "%s %+.0f d" % (key, bb[key][2]), ha="center", fontsize=9, color=col, weight="bold")
axc.set_xticks([1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]); axc.set_xticklabels(list("JFMAMJJASOND"), fontsize=8.5)
axc.set_xlim(1, 365); axc.set_ylim(-0.03, 1.08); axc.grid(alpha=0.25); axc.tick_params(labelsize=8.5)
axc.set_ylabel("Normalised LAI", fontsize=9)
axc.set_title("(c) Boreal land (50–70N, %d cells): seasonal cycle %d–%d" % (boreal_n, A, B), loc="left", fontsize=10)
axc.legend(loc="upper left", fontsize=8, frameon=False)

# (d) bars by latitude band (per-cell statistics)
names = [b[0] for b in BANDS]
x = np.arange(len(names)); wd = 0.36
for j, (key, col, off, k0) in enumerate((("SOS", "#2c7fb8", -wd / 2, 0), ("EOS", "#d95f0e", wd / 2, 3))):
    b = np.array([cellbias[nm][k0] for nm in names]); sp = np.array([cellbias[nm][k0 + 1] for nm in names])
    nn = np.array([cellbias[nm][k0 + 2] for nm in names])
    axd.bar(x + off, b, wd, color=col, alpha=0.85, label="CTRL \u2212 observed mean, %s" % key)
    axd.errorbar(x + off, b, yerr=sp / 2, fmt="none", ecolor="k", elinewidth=1, capsize=3,
                 label="observational spread (max \u2212 min of 3 products)" if j == 0 else None)
    for xi, bi, ni in zip(x + off, b, nn):
        axd.text(xi, bi + sp.max() / 2 + 1.5 if bi >= 0 else bi - 5, "%+.0f" % bi, ha="center", fontsize=8, color=col)
        if ni >= 1:
            axd.text(x[0] - 0.45, -10 if key == "SOS" else -14.5, "CTRL no leaf-off: %s %.0f %% of cells" % (key, ni), ha="left", fontsize=7, color=col)
axd.axhline(0, color="k", lw=0.8)
axd.set_xticks(x); axd.set_xticklabels(names, fontsize=9)
axd.set_ylabel("Bias (days, + = model later)", fontsize=9); axd.yaxis.set_label_position("right"); axd.yaxis.tick_right()
axd.set_title("(d) CTRL SOS and EOS bias by latitude band (cells with an observed season)", loc="left", fontsize=10)
axd.legend(fontsize=7.5, frameon=False, loc="upper left", ncol=1)
axd.grid(axis="y", alpha=0.25); axd.set_ylim(-17, 74)
fig.savefig("../figures/f1_ctrl_bias_regions.png", dpi=200, bbox_inches="tight")
open("../data/f1_sos_eos_bias.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out[-7:]))
