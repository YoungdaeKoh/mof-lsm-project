#!/usr/bin/env python3
"""Spin-up trajectories of the four LSMs on one common panel set (one figure per model).

Panels (same position in every figure): LAI, vegetation C, soil C, soil/column water,
deep soil T, GPP, snow.  Land means over NON-ICE land, area/cos(lat)-weighted
(JULES also drops its 159 perennial-snow cells).  Inputs (all pre-computed CSVs):
  CLM5    data/clm5/clm5_bgc_spinup_annual.csv   annual means, AD 1-210 + post-AD 211-411
          (cesm/scripts/clm5_bgc_spinup_annual.py; AD carbon is in the accelerated state)
  Noah-MP data/noahmp/noahmp_dveg5_spinup_jan1.csv  Jan-1 SNAPSHOTS, 6 cycles x 30 yr
          (noahmp/scripts/noahmp_dveg5_spinup_annual.py; no annual GPP was written)
  LM4p    lm4/data/monthly_noice_30yr.csv  1 cycle 1981-2010 after the KIOST 400-yr IC;
          annual = Jan-Nov mean (Dec missing in 1991-96, notes 13.45); GPP kgC/m2/yr assumed
  JULES   data/jules/ts_c01..03.csv  annual means, 3 cycles x 30 yr (jules/scripts/spinup_timeseries.py)
Output: figures/spinup_4models/<model>_spinup.png
"""
import os
import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = "/Volumes/data01/MOF_LSM_project/"
OUT = R + "figures/spinup_4models/"
os.makedirs(OUT, exist_ok=True)
COL = {"CLM5": "#2a78d6", "Noah-MP": "#eb6834", "LM4p": "#1baf7a", "JULES": "#eda100"}   # fixed model order
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
PANELS = ["LAI", "vegC", "soilC", "water", "soilT", "GPP", "snow"]
YLAB = {"LAI": "m$^2$ m$^{-2}$", "vegC": "kgC m$^{-2}$", "soilC": "kgC m$^{-2}$", "water": "kg m$^{-2}$",
        "soilT": "K", "GPP": "gC m$^{-2}$ d$^{-1}$", "snow": "kg m$^{-2}$"}


def clm5():
    f = R + "data/clm5/clm5_bgc_spinup_annual.csv"
    d = pd.read_csv(f)
    nad = int(d.loc[d.phase == "AD", "year"].max())
    s = {"x": d.year.values, "LAI": d.TLAI, "vegC": d.TOTVEGC, "soilC": d.TOTSOMC, "water": d.TWS,
         "soilT": d.TSOI_deep, "GPP": d.GPP, "snow": d.H2OSNO}
    lab = {"LAI": "TLAI", "vegC": "TOTVEGC", "soilC": "TOTSOMC", "water": "TWS (total water storage)",
           "soilT": "TSOI layer 20", "GPP": "GPP", "snow": "H2OSNO"}
    cyc = [(x + 0.5, None) for x in range(30, nad, 30)] + [(nad + x + 0.5, None) for x in range(30, len(d) - nad, 30)]
    return s, lab, [(nad + 0.5, "AD | post-AD")] + cyc, \
        "CLM5 BGC: AD %d yr + post-AD %d yr, WFDE5 1981-2010 cycling (annual means)" % (nad, len(d) - nad), \
        "AD-phase carbon pools are in the accelerated state (jump at the boundary); AD history has no soil T / soil water / snow."


def noahmp():
    d = pd.read_csv(R + "data/noahmp/noahmp_dveg5_spinup_jan1.csv")
    s = {"x": d.spinyear.values, "LAI": d.LAI, "vegC": d.vegC, "soilC": d.soilC, "water": d.colwater,
         "soilT": d.soilT_deep, "GPP": None, "snow": d.SNEQV}
    lab = {"LAI": "LAI", "vegC": "leaf+stem+wood+root", "soilC": "FASTCP+STBLCP", "water": "SMC, 2 m column",
           "soilT": "SOIL_T layer 4 (1-2 m)", "GPP": "not written in spin-up", "snow": "SNEQV"}
    return s, lab, [(30.5 + 30 * k, None) for k in range(5)], \
        "Noah-MP DVEG=5: 6 cycles x 30 yr, WFDE5 1981-2010 (Jan-1 snapshots)", \
        "Values are 1 January 03Z snapshots, not annual means (output was yearly)."


def lm4p():
    # cycle 1 = spin-up (lm4_spinup30); cycle 2 = ctl production 1981-2010, which starts
    # from the cycle-1 end state redated to 1979 (1979-80 of ctl are skipped here).
    # Both extracted by lm4/scripts/extract_monthly_noice.py (same C96 mask/averaging).
    parts = []
    for f in ("monthly_noice_30yr.csv", "monthly_noice_ctl_1981_2010.csv"):
        m = pd.read_csv(R + "lm4/data/" + f)
        m = m[m.month <= 11]                               # Jan-Nov for every year (notes 13.45)
        parts.append(m.groupby("year").mean(numeric_only=True).reset_index())
    d = pd.concat(parts, ignore_index=True)
    s = {"x": np.arange(1, len(d) + 1), "LAI": d.LAI, "vegC": d.bwood, "soilC": d.soilC, "water": d.col_water,
         "soilT": d.soilT_2m, "GPP": d.GPP * 1000 / 365, "snow": d.SWE}
    lab = {"LAI": "LAI", "vegC": "bwood (wood only)", "soilC": "soilC", "water": "col_water",
           "soilT": "soil T 2 m", "GPP": "GPP", "snow": "SWE"}
    return s, lab, [(30.5, None)], \
        "LM4p (PPA): spin-up cycle 1 + ctl 1981-2010 as cycle 2, after the KIOST-ESM2 400-yr IC (Jan-Nov means)", \
        ("Cycle 2 = ctl production 1981-2010 (ctl starts from the cycle-1 end state). Same-year c2-c1 in 2010: "
         "LAI -0.6 %, GPP +0.4 %, soil T +0.006 K (converged; the within-cycle warming is forcing), "
         "soil C +3.0 %, wood C +7.6 % (still drifting). The preceding 400 years are the KIOST coupled spin-up.")


def jules():
    d = pd.concat([pd.read_csv(R + "data/jules/ts_c%02d.csv" % c) for c in (1, 2, 3)], ignore_index=True)
    s = {"x": np.arange(1, len(d) + 1), "LAI": d.lai, "vegC": d.cv, "soilC": d.cs, "water": d.smc_tot,
         "soilT": d.t_soil, "GPP": d.gpp_gb, "snow": d.snow_mass_gb}
    lab = {"LAI": "LAI (PFT-weighted)", "vegC": "cv", "soilC": "cs (RothC 4 pools)", "water": "smc_tot",
           "soilT": "t_soil bottom layer", "GPP": "gpp_gb", "snow": "snow_mass_gb (perennial-snow cells excluded)"}
    return s, lab, [(30.5, None), (60.5, None)], \
        "JULES TRIFFID: 3 cycles x 30 yr, equilibrium mode, WFDE5 1981-2010 (annual means)", \
        "Cold start (cs = 4 x 10 kgC/m2); the 1982 jump is the first equilibrium TRIFFID update."


def plot(name, fn):
    try:
        s, lab, bounds, title, foot = fn()
    except FileNotFoundError as e:
        print("skip", name, e); return
    fig, axs = plt.subplots(4, 2, figsize=(11, 11), sharex=True)
    axs = axs.ravel()
    for k, p in enumerate(PANELS):
        ax = axs[k]
        y = s[p]
        ax.set_title("%s  [%s]" % ({"LAI": "LAI", "vegC": "Vegetation carbon", "soilC": "Soil carbon",
                                    "water": "Soil / column water", "soilT": "Deep soil temperature",
                                    "GPP": "GPP", "snow": "Snow"}[p], lab[p]), fontsize=9.5, color=INK, loc="left")
        ax.grid(color=GRID, lw=0.6); ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        for sp in ("left", "bottom"):
            ax.spines[sp].set_color(MUTED)
        ax.tick_params(colors=MUTED, labelsize=8.5)
        ax.set_ylabel(YLAB[p], color=MUTED, fontsize=8.5)
        if y is None or np.all(~np.isfinite(np.asarray(y, float))):
            ax.text(0.5, 0.5, "not available", transform=ax.transAxes, ha="center", va="center", color=MUTED)
            continue
        ax.plot(s["x"], np.asarray(y, float), color=COL[name], lw=2)
        for xb, txt in bounds:
            ax.axvline(xb, color=MUTED, lw=0.8, ls="--" if txt is None else "-")
            if txt and k == 0:
                ax.text(xb, 1.0, " " + txt, transform=ax.get_xaxis_transform(), fontsize=8, color=MUTED, va="top")
    axs[-1].axis("off")
    note = foot + "\n\nNon-ice land, area / cos(lat)-weighted land mean."
    if any(t is None for _, t in bounds):
        note += "\nDashed lines: forcing cycle boundaries (30 yr)."
    axs[-1].text(0, 0.95, "\n".join(textwrap.fill(p, 62) if p else p for p in note.split("\n")),
                 fontsize=8.5, color=MUTED, va="top", transform=axs[-1].transAxes)
    for ax in axs[5:7]:
        ax.set_xlabel("spin-up year", color=MUTED, fontsize=9)
    axs[4].set_xlabel("spin-up year", color=MUTED, fontsize=9)
    fig.suptitle(title, fontsize=11.5, color=INK, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    f = OUT + "%s_spinup.png" % name.replace("-", "").lower()
    fig.savefig(f, dpi=150, facecolor="#fcfcfb"); plt.close(fig)
    print("wrote", f)


for n, fn in (("CLM5", clm5), ("Noah-MP", noahmp), ("LM4p", lm4p), ("JULES", jules)):
    plot(n, fn)
