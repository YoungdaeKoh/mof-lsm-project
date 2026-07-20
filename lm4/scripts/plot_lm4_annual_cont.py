#!/opt/homebrew/bin/python3
# LM4 WFDE5 dynamic-veg CONTINUOUS spin-up (300 yr) — ANNUAL-mean global-land time series.
# The forcing loops 1981-2010 every 30 yr, so raw annual series carries a 30-yr oscillation +
# forcing-loop-back spikes (deep-T/sens/evap). A 30-yr running mean (= exactly the forcing
# period) cancels both, leaving the clean convergence trend.
import numpy as np
import matplotlib.pyplot as plt

CSV = "/Volumes/data01/MOF_LSM_project/lm4/data/annual_spinup_cont.csv"
OUT = "/Volumes/data01/MOF_LSM_project/figures/lm4_annual_cont_spinup.png"
W = 30   # running-mean window = forcing cycle length

d = np.genfromtxt(CSV, delimiter=",", names=True)
yr_raw = d["spinup_year"]

# regular 1..max grid, linearly fill the small crashed-segment gap (yr ~101-105)
yg = np.arange(int(yr_raw.min()), int(yr_raw.max()) + 1)

def rmean(v):
    vi = np.interp(yg, yr_raw, v)
    k = np.ones(W) / W
    rm = np.convolve(vi, k, mode="valid")          # len = len(yg)-W+1
    xrm = yg[(W - 1) // 2 : (W - 1) // 2 + len(rm)]
    return xrm, rm

PAN = [
    ("btot",       "Vegetation carbon (btot)",        "kg C m$^{-2}$", "#3a7a37"),
    ("soilC",      "Soil carbon (fast+slow, column)", "kg C m$^{-2}$", "#6b4423"),
    ("colwater",   "Column soil water (liq+ice)",     "kg m$^{-2}$",   "#1f6f8b"),
    ("soilT_deep", "Soil temperature (~2 m)",         "K",             "#b5551a"),
    ("LAI",        "LAI",                             "m$^2$ m$^{-2}$","#4a8c2a"),
    ("nep",        "NEP (→0 at equilibrium)",     "kg C m$^{-2}$", "#8a3a8a"),
    ("sens",       "Sensible heat",                   "W m$^{-2}$",    "#c0392b"),
    ("evap",       "Evaporation",                     "kg m$^{-2}$ s$^{-1}$", "#2874a6"),
]

fig, axes = plt.subplots(4, 2, figsize=(13, 11))
fig.suptitle("LM4 WFDE5 dynamic-veg CONTINUOUS spin-up (300 yr) — ANNUAL global-land mean\n"
             "faint = annual · bold = 30-yr running mean (cancels the forcing-cycle oscillation)",
             fontsize=12.5, fontweight="bold")

for ax, (key, title, unit, col) in zip(axes.flat, PAN):
    v = d[key]
    ax.plot(yr_raw, v, "-", color=col, lw=0.8, alpha=0.22, zorder=2)   # raw annual (faint)
    xrm, rm = rmean(v)
    ax.plot(xrm, rm, "-", color=col, lw=2.2, zorder=3)                 # 30-yr running mean (bold)
    sl = np.polyfit(xrm[-30:], rm[-30:], 1)[0] if len(rm) >= 30 else np.nan
    ax.set_title(title, fontsize=10.5)
    ax.set_ylabel(unit, fontsize=9)
    ax.grid(alpha=.25)
    ax.text(0.97, 0.06, f"end slope(30yrRM)={sl:+.3g}/yr",
            transform=ax.transAxes, fontsize=8, va="bottom", ha="right",
            family="monospace",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=col, alpha=.85))

for ax in axes[-1, :]:
    ax.set_xlabel("cumulative spin-up year")

fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print("saved:", OUT)
for key, title, unit, col in PAN:
    xrm, rm = rmean(d[key])
    print(f"{key:<11} RM {rm[0]:.4g} -> {rm[-1]:.4g}")
