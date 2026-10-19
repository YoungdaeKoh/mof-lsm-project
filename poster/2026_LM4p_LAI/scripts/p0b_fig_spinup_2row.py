#!/usr/bin/env python3
"""LM4p spin-up in two rows: fast variables (LAI, GPP, fast soil C) converge, slow carbon (total soil C, wood) drifts.

Cycles of the WFDE5 1981-2010 forcing, 30 years each, after the KIOST 400-yr coupled IC:
  cycle 1 = lm4_spinup30/archive_c1 (spin-up)
  cycle 2 = lm4p_ctl_1979-2024/archive (ctl, CO2 fixed ~292 ppm)
  cycle 3 = lm4p_ctl2_co2_1979-2023/archive (ctl2_co2, HISTORICAL CO2 338->390 ppm; still running, years present
            locally are plotted) -> not a pure spin-up cycle: its drift includes the CO2 response
Same mask and averaging as lm4/scripts/compare_carbon_pools_cycles.py: C96 points with lai defined minus Greenland,
unweighted mean (cubed sphere ~equal area), Jan-Nov annual mean (cycle 1 years 1981-1996 have no December, notes 13.31).
Row 2 lines: per-cycle linear trend (dashed) and its value in % per 30 yr of the cycle mean.
output: ../figures/fig0b_spinup_2row.png, ../data/spinup_2row_annual.csv
"""
import os
import sys
import numpy as np
from netCDF4 import Dataset
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, "../../../lm4/scripts")
from greenland_mask import in_greenland

L = "/Volumes/data02/LM4P/cases/"
CYC = [("Cycles 1–2: spin-up, CTRL (FixCO2, 292 ppm)", L + "lm4_spinup30/archive_c1"),
       ("", L + "lm4p_ctl_1979-2024/archive"),
       ("HistCO2 run (ctl2_co2; not a spin-up cycle)", L + "lm4p_ctl2_co2_1979-2023/archive")]
VARS = [("lai", "(a) LAI", "m$^2$ m$^{-2}$", 1.0), ("gpp", "(b) GPP", "gC m$^{-2}$ d$^{-1}$", 1000 / 365),
        ("fsc", "(c) Fast soil carbon", "kgC m$^{-2}$", 1.0),
        ("tot_soil_C", "(d) Total soil carbon", "kgC m$^{-2}$", 1.0), ("bwood", "(e) Wood carbon", "kgC m$^{-2}$", 1.0)]
FILL = 1e30
COL = ["#1baf7a", "#1baf7a", "#d9822b"]   # cycle 3 in orange: different CO2 forcing

MASK = {}
for t in range(1, 7):
    d = Dataset(f"{CYC[1][1]}/y2010/20100101.land_month.tile{t}.nc")
    a = np.ma.filled(d.variables["lai"][0].astype("f8"), np.nan); a[np.abs(a) > FILL] = np.nan
    MASK[t] = np.isfinite(a) & ~in_greenland(np.array(d.variables["geolat_t"][:]), np.array(d.variables["geolon_t"][:]))
    d.close()

data = []   # per cycle: dict var -> array over available years
for name, root in CYC:
    yrs = [y for y in range(1981, 2011) if os.path.exists(f"{root}/y{y}/{y}0101.land_month.tile6.nc")]
    v = {k: [] for k, *_ in VARS}
    for y in yrs:
        s = {k: 0.0 for k in v}; c = {k: 0.0 for k in v}
        for t in range(1, 7):
            with Dataset(f"{root}/y{y}/{y}0101.land_month.tile{t}.nc") as d:
                for k in v:
                    a = np.ma.filled(d.variables[k][:11].astype("f8"), np.nan)
                    a[np.abs(a) > FILL] = np.nan
                    a = np.where(MASK[t][None, :], a, np.nan)
                    s[k] += np.nansum(a); c[k] += np.isfinite(a).sum()
        for k in v:
            v[k].append(s[k] / c[k])
    data.append((np.array(yrs), {k: np.array(x) for k, x in v.items()}))
    print("%s: %d years (%d-%d)" % (root.split("/")[-2], len(yrs), yrs[0], yrs[-1]))

rows = ["cycle,year," + ",".join(k for k, *_ in VARS)]
for i, (yrs, v) in enumerate(data):
    rows += ["%d,%d," % (i + 1, y) + ",".join("%.6g" % v[k][j] for k, *_ in VARS) for j, y in enumerate(yrs)]
open("../data/spinup_2row_annual.csv", "w").write("\n".join(rows) + "\n")

fig = plt.figure(figsize=(13, 7.4))
gs = fig.add_gridspec(2, 6, hspace=0.42, wspace=0.9)
axs = [fig.add_subplot(gs[0, 0:2]), fig.add_subplot(gs[0, 2:4]), fig.add_subplot(gs[0, 4:6]),
       fig.add_subplot(gs[1, 0:3]), fig.add_subplot(gs[1, 3:6])]
for p, (ax, (k, title, unit, sc)) in enumerate(zip(axs, VARS)):
    allv = np.concatenate([v[k] for _, v in data]) * sc
    for i, (yrs, v) in enumerate(data):
        x = (yrs - 1980) + 30 * i
        y = v[k] * sc
        ax.plot(x, y, color=COL[i], lw=1.6 if p >= 3 else 1.2, alpha=1 if p >= 3 else 0.8,
                label=CYC[i][0] if (p == 0 and CYC[i][0]) else None)
        if p >= 3:   # slow pools: per-cycle linear trend, % per 30 yr of the cycle mean
            b = np.polyfit(x, y, 1)
            ax.plot(x, np.polyval(b, x), color="0.25", ls="--", lw=1)
            tr = 100 * b[0] * 30 / y.mean()
            lab = ("%+.1f %%/30 yr" % tr) + ("\n(%d yr)" % len(x) if len(x) < 30 else "")
            ax.text(x.mean() + (4 if i == 2 else 0), 0.04, lab.replace("-", "−"), transform=ax.get_xaxis_transform(), ha="center",
                    fontsize=9, color="0.15" if i < 2 else "#a85d12")
    for b_ in (30.5, 60.5):
        ax.axvline(b_, color="0.3", ls="--", lw=1)
    ax.axvspan(60.5, 90.5, color="0.94", lw=0)
    if p < 3:
        m12 = np.concatenate([v[k] for _, v in data[:2]]).mean() * sc
        ax.set_ylim(m12 * 0.8, m12 * 1.2)   # same relative range (+-20 % of the cycle 1-2 mean) in row 1, cycle 3 fits
    else:
        lo, hi = allv.min(), allv.max(); pad = (hi - lo) * 0.25
        ax.set_ylim(lo - pad, hi + pad * 0.6)
    ax.set_xlim(0, 91); ax.set_xticks(range(0, 91, 10))
    ax.set_title(title, loc="left", fontsize=11)
    ax.set_ylabel(unit); ax.set_xlabel("Spin-up year")
    ax.grid(alpha=0.3)
axs[0].legend(loc="upper left", fontsize=7.5, frameon=False)
for i, lab in enumerate(("Cycle 1", "Cycle 2", "HistCO2")):
    axs[3].text(15 + 30 * i, 0.93, lab, transform=axs[3].get_xaxis_transform(), ha="center", fontsize=9, color="0.3")
axs[4].text(0.98, 0.93, "dashed = linear trend per cycle", transform=axs[4].transAxes, ha="right", fontsize=8.5, color="0.3")
fig.savefig("../figures/fig0b_spinup_2row.png", dpi=200, bbox_inches="tight")

# console: per-cycle trend and 2010-equivalent cycle differences
for k, title, *_ in VARS:
    tr = []
    for yrs, v in data:
        tr.append(100 * np.polyfit(yrs, v[k], 1)[0] * 30 / v[k].mean())
    y3 = data[2][0][-1]
    d32 = 100 * (data[2][1][k][-1] / data[1][1][k][data[1][0] == y3][0] - 1)
    print("%-24s trend %%/30yr c1 %+6.2f c2 %+6.2f c3 %+6.2f (%d yr) | c3-c2 at %d %+6.2f %%"
          % (title, *tr, len(data[2][0]), y3, d32))
