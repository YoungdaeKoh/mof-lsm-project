#!/usr/bin/env python3
"""Fig. 3: why CTRL is late - the phenology rules reconstructed cell by cell from daily canopy temperature, 2010.

Rules (vegn_dynamics.F90 vegn_phenology_ppa, larix/c3grass parameters: gdd_crit 180, tc_crit 5 C):
  leaf-on  : GDD > 180  AND  tc_pheno >= 5 C  AND  soil not dry/frozen,  tc_pheno = 20-day EMA of canopy T
  leaf-off : tc_pheno < 5 C  (CTRL);  patch adds: days shortening AND day length < 13 h AND tc_pheno < 20 C
Daily input: dayl_d 2010 land_daily (vegn_temp_max/min, soil_liq/ice, lai); spring rules in dayl_d = CTRL.
(a) spring delay produced by the 20-day smoothing: doy(tc_pheno >= 5 C) - doy(5-day mean T >= 5 C)
(b) spring: the gate that opens last (binding): GDD / smoothed temperature / soil thaw (top 10 cm liquid fraction >= 0.3)
(c) autumn: doy(day length < 13 h, shortening) - doy(tc_pheno < 5 C): how much earlier the photoperiod rule fires
(d) autumn: doy(tc_pheno < 5 C) - observed EOS (GIMMS 2010, 50 % amplitude): lateness of the CTRL cold rule
C96 land points binned to 1 deg (mean); cells 20-80N with LAI seasonal range > 0.3 in dayl_d.
output: ../figures/f3_rule_timing_maps.png, ../data/f3_rule_timing_bands.txt
"""
import glob
import numpy as np
from netCDF4 import Dataset
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature

RUN = "/Volumes/data02/LM4P/cases/phentest_2010/dayl_d/"
OBS = "../../../poster/2026_LM4p_LAI/data/gimms_lai_mon_1982_2020.nc"
V = ("lai", "vegn_temp_max", "vegn_temp_min", "soil_liq", "soil_ice")
d = {k: [] for k in V}; lat = []; lon = []
for f in sorted(glob.glob(RUN + "*.land_daily.tile*.nc")):
    with Dataset(f) as A:
        A.set_auto_mask(False)
        la = A["geolat_t"][:].ravel(); lo = A["geolon_t"][:].ravel()
        m = (la >= 20) & (la <= 80)
        lat.append(la[m]); lon.append(lo[m])
        for k in V:
            x = A[k][:].astype("f8")
            x = x.reshape(x.shape[0], -1, m.size) if x.ndim == 3 else x.reshape(x.shape[0], m.size)
            d[k].append(x[..., m])
lat = np.concatenate(lat); lon = np.concatenate(lon); lon = np.where(lon > 180, lon - 360, lon)
d = {k: np.concatenate(v, axis=-1) for k, v in d.items()}
nt = d["lai"].shape[0]
ok = np.all((d["lai"] >= 0) & (d["lai"] < 1e10), 0) & np.all((d["vegn_temp_max"] > 100) & (d["vegn_temp_max"] < 400), 0) \
     & np.all(np.abs(d["soil_liq"]) < 1e10, (0, 1)) & ((d["lai"].max(0) - d["lai"].min(0)) > 0.3)
doy = np.arange(1, nt + 1)[:, None]


def first(cond, start=60):
    c = cond & (doy > start)
    return np.where(c.any(0), np.argmax(c, 0) + 1.0, np.nan)


Tx, Tn = d["vegn_temp_max"] - 273.15, d["vegn_temp_min"] - 273.15
tm = (Tx + Tn) / 2
gdd = np.cumsum((np.maximum(Tn, 0) + np.maximum(Tx, 0)) / 2, 0)
tc = np.empty_like(tm); tc[0] = tm[:31].mean(0)
for t in range(1, nt):
    tc[t] = 0.95 * tc[t - 1] + 0.05 * tm[t]
t5 = np.apply_along_axis(lambda a: np.convolve(a, np.ones(5) / 5, "same"), 0, tm)
dz = np.array([0.02, 0.04, 0.04]); z = np.array([0.01, 0.04, 0.08]); wz = dz * np.exp(-z / 0.3); wz /= wz.sum()
liq = d["soil_liq"] / 1000.0; tot = (d["soil_liq"] + d["soil_ice"]) / 1000.0
theta = (np.minimum(liq / np.maximum(tot.max(0), 1e-3), 1.0) * wz[None, :, None]).sum(1)
th = np.empty_like(theta); th[0] = theta[0]
for t in range(1, nt):
    th[t] = th[t - 1] + (theta[t] - th[t - 1]) / 31.0

g_gdd = first(gdd > 180, 0); g_tc = first(tc >= 5); g_th = first(th >= 0.3); g_raw = first(t5 >= 5)
binding = np.argmax(np.vstack([g_gdd, g_tc, g_th]), 0).astype(float)   # 0 GDD, 1 tc, 2 thaw
rl = np.radians(lat)[None, :]
decl = np.radians(23.44) * np.sin(2 * np.pi * (284 + doy) / 365)
dayl = 24 / np.pi * np.arccos(np.clip(-np.tan(rl) * np.tan(decl), -1, 1))
shorten = (rl * np.cos(2 * np.pi * (284 + doy) / 365)) < 0
after = doy > 172
cold = np.where((after & (tc < 5)).any(0), np.argmax(after & (tc < 5), 0) + 1.0, np.nan)
dl13 = np.where((after & shorten & (dayl < 13) & (tc < 20)).any(0), np.argmax(after & shorten & (dayl < 13) & (tc < 20), 0) + 1.0, np.nan)

# observed EOS 2010 per 1-deg cell (50 % amplitude, monthly interpolated), mapped to the C96 points
MID = np.array([15.5, 45, 74.5, 105, 135.5, 166, 196.5, 227.5, 258, 288.5, 319, 349.5]); D = np.arange(1, 366.0)
with Dataset(OBS) as A:
    gv = [v for v in A.variables if A.variables[v].ndim == 3][0]
    G = np.ma.filled(A[gv][(2010 - 1982) * 12:(2010 - 1982) * 12 + 12].astype("f8"), np.nan)
G[np.abs(G) > 100] = np.nan
eos_obs_1deg = np.full((180, 360), np.nan)
for i, j in zip(*np.where(np.isfinite(G).all(0) & ((G.max(0) - G.min(0)) >= 0.5))):
    mm = G[:, i, j]; c = np.interp(D, np.r_[MID[-1] - 365, MID, MID[0] + 365], np.r_[mm[-1], mm, mm[0]])
    thr = c.min() + 0.5 * np.ptp(c); ip = int(c.argmax()); dn = [k for k in range(ip, 364) if c[k] >= thr > c[k + 1]]
    if dn:
        k = dn[0]; eos_obs_1deg[i, j] = D[k] + (c[k] - thr) / (c[k] - c[k + 1])
ii = np.clip(((lat + 90) // 1).astype(int), 0, 179); jj = np.clip(((lon + 180) // 1).astype(int), 0, 359)
eos_obs = eos_obs_1deg[ii, jj]

fields = {"a": g_tc - g_raw, "b": binding, "c": dl13 - cold, "d": cold - eos_obs}
# bin C96 points to 1 deg (mean; mode for the category field)
def to1deg(v, mask, mode=False):
    out = np.full((180, 360), np.nan)
    if mode:
        cnt = np.zeros((180, 360, 3))
        for k in range(3):
            np.add.at(cnt[:, :, k], (ii[mask & (v == k)], jj[mask & (v == k)]), 1)
        has = cnt.sum(2) > 0; out[has] = cnt.argmax(2)[has]
    else:
        s = np.zeros((180, 360)); n = np.zeros((180, 360)); mk = mask & np.isfinite(v)
        np.add.at(s, (ii[mk], jj[mk]), v[mk]); np.add.at(n, (ii[mk], jj[mk]), 1); out[n > 0] = s[n > 0] / n[n > 0]
    return out


maps = {k: to1deg(v, ok, mode=(k == "b")) for k, v in fields.items()}
lat1 = -89.5 + np.arange(180); lon1 = -179.5 + np.arange(360)
# fill 1-deg boxes that received no C96 point from the nearest point (within 1.5 deg), only where GIMMS has a season
from scipy.spatial import cKDTree
tree = cKDTree(np.c_[lat[ok], lon[ok]])
gy, gx = np.meshgrid(lat1, lon1, indexing="ij")
want = np.isfinite(eos_obs_1deg) & (gy >= 20)
for k in maps:
    hole = want & ~np.isfinite(maps[k])
    dist, idx = tree.query(np.c_[gy[hole], gx[hole]])
    vals = fields[k][ok][idx]
    vals[dist > 1.5] = np.nan
    maps[k][hole] = vals
    maps[k][~want] = np.nan          # show only cells with an observed season (as Fig. 1d)

out = ["Rule timing from dayl_d 2010 daily canopy temperature, C96 cells 20-80N with LAI range > 0.3; medians per latitude band",
       "%-7s %6s | %8s %8s %8s | %6s %6s %6s | %8s %8s %8s" % ("band", "cells", "tc-raw5", "DL13-cold", "cold-obsEOS", "GDD%", "tc%", "thaw%", "raw5", "tc5", "cold")]
for a, b in ((20, 40), (40, 50), (50, 60), (60, 70), (70, 80)):
    m = ok & (lat >= a) & (lat < b)
    if m.sum() < 20:
        continue
    out.append("%2d-%2dN %6d | %8.0f %8.0f %8.0f | %6.0f %6.0f %6.0f | %8.0f %8.0f %8.0f" % (
        a, b, m.sum(), np.nanmedian(fields["a"][m]), np.nanmedian(fields["c"][m]), np.nanmedian(fields["d"][m]),
        *[100 * np.mean(binding[m] == k) for k in range(3)], np.nanmedian(g_raw[m]), np.nanmedian(g_tc[m]), np.nanmedian(cold[m])))
open("../data/f3_rule_timing_bands.txt", "w").write("\n".join(out) + "\n"); print("\n".join(out))

proj = ccrs.PlateCarree(central_longitude=180)
fig, axs = plt.subplots(2, 2, figsize=(13, 5.6), subplot_kw={"projection": proj}, gridspec_kw={"hspace": 0.02, "wspace": 0.06})
spec = [("a", "(a) Spring: leaf-on delay from the 20-day temperature smoothing (days)", "YlOrRd", 0, 50, "days"),
        ("b", "(b) Spring: the last gate to open (binding condition)", None, None, None, None),
        ("c", "(c) Autumn: photoperiod rule (13 h) minus cold rule (5 °C) leaf-off date (days)", "RdBu", -90, 90, "days (negative = photoperiod earlier)"),
        ("d", "(d) Autumn: CTRL cold-rule leaf-off minus observed EOS (days)", "RdBu_r", -60, 60, "days (positive = CTRL later)")]
for ax, (k, title, cmap, lo, hi, lab) in zip(axs.ravel(), spec):
    ax.set_extent([-180, 180, 20, 80], crs=proj)
    ax.coastlines(lw=0.4, color="0.3"); ax.add_feature(cfeature.OCEAN, facecolor="#eef3f7", zorder=0)
    if k == "b":
        cm = ListedColormap(["#1b9e77", "#d95f02", "#7570b3"]); nm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5], 3)
        im = ax.pcolormesh(lon1, lat1, np.ma.masked_invalid(maps[k]), cmap=cm, norm=nm, transform=ccrs.PlateCarree(), shading="auto")
        cb = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.08, shrink=0.55, aspect=30, ticks=[0, 1, 2])
        cb.ax.set_xticklabels(["GDD > 180", "smoothed T ≥ 5 °C", "soil thaw"], fontsize=8)
    else:
        im = ax.pcolormesh(lon1, lat1, np.ma.masked_invalid(maps[k]), cmap=cmap, vmin=lo, vmax=hi, transform=ccrs.PlateCarree(), shading="auto")
        cb = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.08, shrink=0.55, aspect=30); cb.set_label(lab, fontsize=8); cb.ax.tick_params(labelsize=7.5)
    gl = ax.gridlines(draw_labels=True, lw=0.3, color="0.6", ls=":", xlocs=range(-180, 181, 60), ylocs=range(20, 81, 20))
    gl.top_labels = False; gl.right_labels = False; gl.xlabel_style = {"size": 7.5}; gl.ylabel_style = {"size": 7.5}
    ax.set_title(title, loc="left", fontsize=9)
fig.savefig("../figures/f3_rule_timing_maps.png", dpi=200, bbox_inches="tight")
