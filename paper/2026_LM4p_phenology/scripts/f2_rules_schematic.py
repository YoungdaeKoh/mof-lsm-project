#!/usr/bin/env python3
"""Fig. 2 (draft): the leaf phenology rules of LM4.1 (CTRL) and the modified rules, and how they play out in one year.

(a) decision rules, CTRL vs modified (text boxes; changed terms highlighted). Species values: larix / c3grass
    gdd_crit 180, tc_crit 5 C, dayl_crit_off 13 h; acer 360, 10 C, 12 h; tc_crit_off 20 C; dayl_crit_on 12 h.
(b) one boreal cell (nearest C96 land point to LAT0, LON0) in 2010 from the dayl_d daily output:
    canopy temperature (daily mean, 20-day EMA as in the model, 5-day EMA of the patch), the 5 C threshold, GDD-180
    date, day length with the 13 h / 12 h lines, and the resulting leaf-on / leaf-off dates of CTRL (cold rule
    reconstructed) and of the modified rules (dayl_d daily LAI shows the actual leaf-off); observed SOS/EOS (GIMMS 2010,
    50 % amplitude of the 1-deg cell) as arrows.
output: ../figures/f2_rules_schematic.png
"""
import glob
import numpy as np
from netCDF4 import Dataset
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LAT0, LON0 = 58.0, 110.0       # central Siberia (ESB)
RUN = "/Volumes/data02/LM4P/cases/phentest_2010/dayl_d/"
OBS = "../../../poster/2026_LM4p_LAI/data/gimms_lai_mon_1982_2020.nc"

# ---- pick the cell
best = None
for f in sorted(glob.glob(RUN + "*.land_daily.tile*.nc")):
    with Dataset(f) as A:
        A.set_auto_mask(False)
        la = A["geolat_t"][:].ravel(); lo = A["geolon_t"][:].ravel(); lo = np.where(lo > 180, lo - 360, lo)
        lai = A["lai"][:].astype("f8").reshape(365, -1)
        okc = np.all((lai >= 0) & (lai < 1e10), 0) & ((lai.max(0) - lai.min(0)) > 0.3)
        dist = np.hypot(la - LAT0, (lo - LON0) * np.cos(np.radians(LAT0))); dist[~okc] = 1e9
        k = int(dist.argmin())
        if best is None or dist[k] < best[0]:
            tx = A["vegn_temp_max"][:].astype("f8").reshape(365, -1)[:, k] - 273.15
            tn = A["vegn_temp_min"][:].astype("f8").reshape(365, -1)[:, k] - 273.15
            best = (dist[k], la[k], lo[k], lai[:, k], tx, tn)
_, clat, clon, lai, tx, tn = best
tm = (tx + tn) / 2; doy = np.arange(1, 366)
tc20 = np.empty(365); tc20[0] = tm[:31].mean()
tc5 = np.empty(365); tc5[0] = tm[:5].mean()
for t in range(1, 365):
    tc20[t] = 0.95 * tc20[t - 1] + 0.05 * tm[t]; tc5[t] = 0.8 * tc5[t - 1] + 0.2 * tm[t]
gdd = np.cumsum((np.maximum(tn, 0) + np.maximum(tx, 0)) / 2)
decl = np.radians(23.44) * np.sin(2 * np.pi * (284 + doy) / 365)
dayl = 24 / np.pi * np.arccos(np.clip(-np.tan(np.radians(clat)) * np.tan(decl), -1, 1))
shorten = np.cos(2 * np.pi * (284 + doy) / 365) < 0
first = lambda c, start=60: doy[(c & (doy > start))][0] if (c & (doy > start)).any() else np.nan
d_gdd = first(gdd > 180, 0); d_tc20 = first(tc20 >= 5); d_tc5 = first(tc5 >= 5)
on_ctrl = max(d_gdd, d_tc20); on_new = max(d_gdd, d_tc5)
off_cold = first((tc20 < 5), 172); off_dl = first(shorten & (dayl < 13) & (tc20 < 20), 172)
lai_drop = first(lai < lai.max() - 0.5 * (lai.max() - lai.min()), int(np.argmax(lai)))   # dayl_d actual 50 % drop
with Dataset(OBS) as A:
    gv = [v for v in A.variables if A.variables[v].ndim == 3][0]
    i = int(np.clip((clat + 90) // 1, 0, 179)); j = int(np.clip((clon + 180) // 1, 0, 359))
    G = np.ma.filled(A[gv][(2010 - 1982) * 12:(2010 - 1982) * 12 + 12, i, j].astype("f8"), np.nan)
MID = np.array([15.5, 45, 74.5, 105, 135.5, 166, 196.5, 227.5, 258, 288.5, 319, 349.5])
c = np.interp(doy, np.r_[MID[-1] - 365, MID, MID[0] + 365], np.r_[G[-1], G, G[0]]); thr = c.min() + 0.5 * np.ptp(c); ip = int(c.argmax())
sos_obs = doy[[k for k in range(ip) if c[k] < thr <= c[k + 1]][-1]]; eos_obs = doy[[k for k in range(ip, 364) if c[k] >= thr > c[k + 1]][0]]
print("cell %.1fN %.1fE | GDD180 %d, T20>=5 %d, T5>=5 %d -> on CTRL %d, new %d | cold<5 %d, DL13 %d, dayl_d LAI 50%% drop %d | obs SOS %d EOS %d"
      % (clat, clon, d_gdd, d_tc20, d_tc5, on_ctrl, on_new, off_cold, off_dl, lai_drop, sos_obs, eos_obs))

# ---- figure
fig = plt.figure(figsize=(14, 7.4))
gs = fig.add_gridspec(1, 2, width_ratios=(1.0, 1.2), wspace=0.06)
ax = fig.add_subplot(gs[0, 0]); ax.axis("off")
ax.set_title("(a) Leaf phenology rules (deciduous species)", loc="left", fontsize=11)
RED = "#c0392b"; BLK = "0.15"


def box(ax, x, y, w, h, title, lines, colors):
    ax.add_patch(plt.Rectangle((x, y), w, h, fc="white", ec="0.3", lw=1.2, transform=ax.transAxes))
    ax.text(x + 0.02, y + h - 0.025, title, transform=ax.transAxes, fontsize=10.5, weight="bold", va="top")
    for n, (ln, col) in enumerate(zip(lines, colors)):
        ax.text(x + 0.03, y + h - 0.07 - 0.046 * n, ln, transform=ax.transAxes, fontsize=8.6, va="top", color=col, family="monospace")


box(ax, 0.02, 0.66, 0.96, 0.32, "CTRL (LM4.1 release)",
    ["LEAF ON   if  GDD > gdd_crit", "          and T_20d >= tc_crit", "          and soil water >= theta_crit",
     "LEAF OFF  if  T_20d < tc_crit", "          or  drought"],
    [BLK] * 5)
box(ax, 0.02, 0.06, 0.96, 0.56, "Modified (this study)",
    ["LEAF ON   if  GDD > gdd_crit",
     "          and T_5d >= tc_crit            [spring]",
     "          and soil water >= theta_crit",
     "          and not (dayl < 12 h and",
     "                   T_20d < 20 C)         [winter hold]",
     "LEAF OFF  if  T_20d < tc_crit",
     "          or  drought",
     "          or  (days shortening and",
     "               dayl < 13 h and",
     "               T_20d < 20 C)             [autumn]"],
    [BLK, RED, BLK, RED, RED, BLK, BLK, RED, RED, RED])
ax.text(0.02, 0.0, "T_20d / T_5d: canopy temperature smoothed over 20 / 5 days (exponential).\n"
        "gdd_crit 180 (larix, C3 grass) or 360 (acer); tc_crit 5 or 10 \u00b0C;\n"
        "dayl threshold 13 h (larix, C3 grass) or 12 h (acer). Evergreen (picea) and tropical species unchanged.",
        transform=ax.transAxes, fontsize=7.4, color="0.3", va="top")

# (b) timeline
gsb = gs[0, 1].subgridspec(3, 1, height_ratios=(1.3, 1, 0.75), hspace=0.08)
b1 = fig.add_subplot(gsb[0]); b2 = fig.add_subplot(gsb[1], sharex=b1); b3 = fig.add_subplot(gsb[2], sharex=b1)
b1.plot(doy, tm, color="0.7", lw=0.8, label="canopy T, daily")
b1.plot(doy, tc20, color="#1f77b4", lw=2, label="20-day smoothed (CTRL)")
b1.plot(doy, tc5, color="#ff7f0e", lw=1.6, label="5-day smoothed (modified)")
b1.axhline(5, color="k", lw=0.8, ls=":"); b1.text(3, 6, "tc_crit = 5 °C", fontsize=8)
b1.axvline(d_gdd, color="0.4", lw=1, ls="--"); b1.text(d_gdd + 2, b1.get_ylim()[0] + 2 if False else -22, "GDD = 180", fontsize=8, color="0.4")
b1.set_ylabel("°C", fontsize=9); b1.set_ylim(-30, 25); b1.legend(fontsize=7.5, frameon=False, loc="upper left", ncol=1)
b1.set_title("(b) One boreal cell, 2010  (%.1f°N, %.1f°E; dayl_d daily output)" % (clat, clon), loc="left", fontsize=11)
b1.grid(alpha=0.25); plt.setp(b1.get_xticklabels(), visible=False)
b2.plot(doy, dayl, color="#2ca02c", lw=2, label="day length")
b2.axhline(13, color="k", lw=0.8, ls=":"); b2.text(3, 13.3, "13 h (autumn leaf-off)", fontsize=8)
b2.axhline(12, color="k", lw=0.8, ls=":"); b2.text(3, 11.1, "12 h (winter hold)", fontsize=8)
b2.axvline(172, color="0.4", lw=0.8, ls="--"); b2.text(174, 5.5, "solstice", fontsize=8, color="0.4")
b2.set_ylabel("hours", fontsize=9); b2.set_ylim(4, 21); b2.grid(alpha=0.25); plt.setp(b2.get_xticklabels(), visible=False)
# leaf state bars
rows = [("Observed (GIMMS, 50 %)", sos_obs, eos_obs, "0.3"), ("CTRL rules", on_ctrl, off_cold, "#1f77b4"), ("Modified rules", on_new, off_dl, "#d62728")]
for n, (name, a, b, col) in enumerate(rows):
    y = 2 - n
    b3.barh(y, b - a, left=a, height=0.55, color=col, alpha=0.75)
    b3.text(a - 3, y, "%d" % a, ha="right", va="center", fontsize=8, color=col); b3.text(b + 3, y, "%d" % b, ha="left", va="center", fontsize=8, color=col)
b3.set_yticks([2, 1, 0]); b3.set_yticklabels([r[0] for r in rows], fontsize=8.5); b3.set_ylim(-0.6, 2.6)
b3.set_xticks([1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]); b3.set_xticklabels(list("JFMAMJJASOND")); b3.set_xlim(1, 365)
b3.text(0.99, 0.05, "leaf-on = GDD and temperature gates both open; leaf-off = first rule that fires", transform=b3.transAxes, ha="right", fontsize=7, color="0.4")
b3.grid(axis="x", alpha=0.25)
fig.savefig("../figures/f2_rules_schematic.png", dpi=200, bbox_inches="tight")
