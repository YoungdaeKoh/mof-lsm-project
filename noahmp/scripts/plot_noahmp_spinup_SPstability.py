#!/opt/homebrew/bin/python3
# Noah-MP spin-up STATE-equilibrium check, in the CLM SpinupStability_SP visual format.
# Purpose: confirm each model reached equilibrium AT THOSE DEPTHS in its own state -- not a
# cross-model comparison, so depths need only be similar, not identical.
#
# Cycle 2 (30 yr) started from the spun-up seed, so flat curves inside a tight band = stays
# at equilibrium. Only STATE variables are shown: Noah-MP's annual output is a single Jan-01
# 00:00 instantaneous sample, so its HFX/LH/GPP are winter-midnight values (negative fluxes,
# GPP=fill) and are NOT usable -- those would need a monthly-mean rerun. State vars are robust.
# Layers: soil water layer 3 (node 0.70 m) ~ CLM 0.80 m; soil temp layer 4 (node 1.50 m) ~ CLM 1.36 m.
import numpy as np
import matplotlib.pyplot as plt

CSV = "/Volumes/data01/MOF_LSM_project/noahmp/data/noahmp_spinup_SPstability_cyc2.csv"
OUT = "/Volumes/data01/MOF_LSM_project/figures/noahmp_spinup_SPstability.png"

d = np.genfromtxt(CSV, delimiter=",", names=True)
sy = np.arange(1, len(d["year"]) + 1)   # spin-up year within cycle 2

PAN = [
    ("SM_L3", "Soil water — layer 3 (node 0.70 m)",  "m³ m$^{-3}$", "#7d3c98"),
    ("ST_L4", "Soil temperature — layer 4 (node 1.50 m)", "K",      "#117a8b"),
    ("TWS",   "Total water storage (soil + snow + aquifer)", "mm",  "#b5791a"),
    ("SWE",   "Snow water equivalent",               "mm",          "#2471a3"),
]

fig, axes = plt.subplots(2, 2, figsize=(11, 7))
fig.suptitle(
    "Noah-MP spin-up stability  (GSWP3 1°, static veg DVEG=4, cycle 2 from spun-up seed)  —  "
    "state variables, area-weighted",
    fontsize=12, fontweight="bold")

for ax, (key, title, unit, col) in zip(axes.flat, PAN):
    y = d[key]
    eqm, eqs = y[-10:].mean(), y[-10:].std()
    ax.axhspan(eqm - eqs, eqm + eqs, color=col, alpha=.10)
    ax.axhline(eqm, color=col, ls=":", lw=1.4)
    ax.plot(sy, y, "-o", color=col, lw=1.7, ms=3.2)
    ax.set_title(title, fontsize=10.5)
    ax.set_ylabel(unit, fontsize=9.5)
    ax.grid(alpha=.25)
    d5 = np.abs(np.diff(y))[-5:].mean()
    net = y[-1] - y[0]
    ax.text(0.03, 0.06, f"eq {eqm:.4g}\n|Δ/yr|₅ {d5:.3g}\nnet(30yr) {net:+.3g}",
            transform=ax.transAxes, fontsize=8, va="bottom", family="monospace",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=col, alpha=.85))

for ax in axes[1, :]:
    ax.set_xlabel("spin-up year (cycle 2)")

fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print("saved:", OUT)
print(f"{'var':<8}{'equilibrium':>13}{'|Δ/yr| last5':>14}{'net 30yr':>11}")
for key, title, unit, col in PAN:
    y = d[key]
    print(f"{key:<8}{y[-10:].mean():>13.4g}{np.abs(np.diff(y))[-5:].mean():>14.4g}{y[-1]-y[0]:>+11.3g}")
