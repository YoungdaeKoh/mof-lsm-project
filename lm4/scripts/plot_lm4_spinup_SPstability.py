#!/opt/homebrew/bin/python3
# LM4 spin-up STATE-equilibrium check in the CLM SpinupStability_SP visual format.
# Per-model equilibrium check at depth (not a cross-model comparison), so depths need only
# be similar to CLM's 0.80 m / 1.36 m. These 29 annual Jan-01 soil.res restarts are the FINAL
# 30-yr segment of the 300-yr spin-up (cycle 10), so flat curves inside tight bands confirm
# equilibrium. 6 tiles concatenated, unweighted land mean (cubed sphere ~ equal area).
# Layers (zfull node): soil water 0.70 m, soil temp 1.20 m. (LM4 groundwater is 0 here -> omitted.)
import numpy as np
import matplotlib.pyplot as plt

CSV = "/Volumes/data01/MOF_LSM_project/lm4/data/lm4_spinup_SPstability.csv"
OUT = "/Volumes/data01/MOF_LSM_project/figures/lm4_spinup_SPstability.png"

d = np.genfromtxt(CSV, delimiter=",", names=True)
sy = np.arange(1, len(d["year"]) + 1)

PAN = [
    ("SW_070",      "Soil water — 0.70 m layer",  "kg m$^{-2}$", "#7d3c98"),
    ("ST_120",      "Soil temperature — 1.20 m layer", "K",      "#117a8b"),
    ("colwater",    "Column soil water (all layers)", "kg m$^{-2}$", "#b5791a"),
]

fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.3))
fig.suptitle(
    "LM4 spin-up stability  (GSWP3 C96, static veg, final 30-yr segment of 300-yr spin-up)  —  "
    "state variables, land mean",
    fontsize=12, fontweight="bold")

for ax, (key, title, unit, col) in zip(axes, PAN):
    y = d[key]
    eqm, eqs = y[-10:].mean(), y[-10:].std()
    ax.axhspan(eqm - eqs, eqm + eqs, color=col, alpha=.10)
    ax.axhline(eqm, color=col, ls=":", lw=1.4)
    ax.plot(sy, y, "-o", color=col, lw=1.7, ms=3.4)
    ax.set_title(title, fontsize=10.5)
    ax.set_ylabel(unit, fontsize=9.5)
    ax.set_xlabel("year within final segment")
    ax.grid(alpha=.25)
    d5 = np.abs(np.diff(y))[-5:].mean()
    net = y[-1] - y[0]
    ax.text(0.03, 0.06, f"eq {eqm:.4g}\n|Δ/yr|₅ {d5:.3g}\nnet(29yr) {net:+.3g}",
            transform=ax.transAxes, fontsize=8.5, va="bottom", family="monospace",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=col, alpha=.85))

fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print("saved:", OUT)
for key, title, unit, col in PAN:
    y = d[key]
    print(f"{key:<10} eq {y[-10:].mean():.4g}  |Δ/yr|last5 {np.abs(np.diff(y))[-5:].mean():.4g}  net29 {y[-1]-y[0]:+.3g}")
