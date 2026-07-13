#!/opt/homebrew/bin/python3
# LM4 FULL 300-yr spin-up convergence, from the archived IC milestones (soil.res at each
# 30-yr segment end). Cold-start -> equilibrium, the true LM4 spin-up view (the earlier
# figure showed only the final 30-yr segment). State variables at similar depths to CLM:
# soil water 0.70 m, soil temperature 1.20 m, column soil water. 6 tiles, land mean.
#
# NOTE: milestones are instantaneous Jan-01 restart snapshots (IC archives store restarts,
# not annual means), 30-yr spacing -- valid for the long-term convergence curve. The final
# segment's land_annual (annual means) confirms the tail is flat (lm4_spinup_SPstability).
import numpy as np
import matplotlib.pyplot as plt

CSV = "/Volumes/data01/MOF_LSM_project/lm4/data/lm4_spinup_300yr.csv"
OUT = "/Volumes/data01/MOF_LSM_project/figures/lm4_spinup_300yr.png"

d = np.genfromtxt(CSV, delimiter=",", names=True)
yr = d["year"]

PAN = [
    ("SW_070",   "Soil water — 0.70 m layer",      "kg m$^{-2}$", "#7d3c98"),
    ("ST_120",   "Soil temperature — 1.20 m layer", "K",          "#117a8b"),
    ("colwater", "Column soil water (all layers)",  "kg m$^{-2}$", "#b5791a"),
]

fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.3))
fig.suptitle(
    "LM4 spin-up convergence  (GSWP3 C96, static veg, full 300-yr spin-up)  —  "
    "30-yr milestone snapshots, land mean",
    fontsize=12, fontweight="bold")

for ax, (key, title, unit, col) in zip(axes, PAN):
    y = d[key]
    eqm = y[-3:].mean()                                   # equilibrium = last 3 milestones (240-300)
    ax.axhline(eqm, color=col, ls=":", lw=1.4)
    ax.plot(yr, y, "-o", color=col, lw=1.8, ms=5)
    ax.set_title(title, fontsize=10.5)
    ax.set_ylabel(unit, fontsize=9.5)
    ax.set_xlabel("spin-up year")
    ax.set_xticks(np.arange(0, 301, 60))
    ax.grid(alpha=.25)
    d_last = abs(y[-1] - y[-2]) / (yr[-1] - yr[-2])       # drift per year over final 30 yr
    ax.text(0.97, 0.06, f"eq {eqm:.4g}\nfinal drift {d_last:.3g}/yr",
            transform=ax.transAxes, fontsize=8.5, va="bottom", ha="right", family="monospace",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=col, alpha=.85))

fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print("saved:", OUT)
for key, title, unit, col in PAN:
    y = d[key]
    print(f"{key:<10} 30yr {y[0]:.3g} -> 300yr {y[-1]:.3g}  final drift {abs(y[-1]-y[-2])/30:.4g}/yr")
