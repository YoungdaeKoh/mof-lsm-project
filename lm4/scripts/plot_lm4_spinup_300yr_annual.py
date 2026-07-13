#!/opt/homebrew/bin/python3
# LM4 full 300-yr spin-up at ANNUAL resolution, from each segment's land_annual (FMS annual
# means). ~261 annual points; the 91-120 segment (y120) was never archived, so that block is
# a gap (line breaks). Variables that exist annually in LM4 (4 of CLM5's 6 -- sensible & latent
# heat were not in the spin-up diag_table): soil water 0.70 m, soil temp 1.20 m, column water,
# NEP (net productivity; LM4 writes NEP not gross GPP). soil_liq/ice kg/m3 -> volumetric /1000.
import numpy as np
import matplotlib.pyplot as plt

CSV = "/Volumes/data01/MOF_LSM_project/lm4/data/lm4_spinup_300yr_annual.csv"
OUT = "/Volumes/data01/MOF_LSM_project/figures/lm4_spinup_300yr_annual.png"

d = np.genfromtxt(CSV, delimiter=",", names=True)
# place on a full 1..300 grid so gaps break the line
full = np.arange(1, 301)
def grid(key, scale=1.0):
    out = np.full(full.shape, np.nan)
    idx = (d["year"].astype(int) - 1)
    out[idx] = d[key] * scale
    return out

PAN = [
    ("SW_070",   0.001, "Soil water — 0.70 m layer",       "m³ m$^{-3}$", "#7d3c98"),
    ("ST_120",   1.0,   "Soil temperature — 1.20 m layer", "K",           "#117a8b"),
    ("colwater", 1.0,   "Column soil water (all layers)",  "kg m$^{-2}$", "#b5791a"),
    ("NEP",      1.0,   "NEP — net ecosystem productivity", "kg C m$^{-2}$ yr$^{-1}$", "#3a7a37"),
]

fig, axes = plt.subplots(2, 2, figsize=(12.5, 7))
fig.suptitle(
    "LM4 spin-up convergence  (GSWP3 C96, static veg, full 300-yr, ANNUAL resolution)  —  "
    "land_annual means; 91–120 not archived",
    fontsize=12, fontweight="bold")

for ax, (key, sc, title, unit, col) in zip(axes.flat, PAN):
    y = grid(key, sc)
    fin = np.isfinite(y)
    eqm = np.nanmean(y[-40:][np.isfinite(y[-40:])])
    ax.axhline(eqm, color=col, ls=":", lw=1.3)
    ax.plot(full, y, "-", color=col, lw=1.4)
    ax.plot(full[fin], y[fin], "o", color=col, ms=2.4)
    ax.axvspan(90, 120, color="0.5", alpha=.12)         # missing block
    ax.set_title(title, fontsize=10.5)
    ax.set_ylabel(unit, fontsize=9.5)
    ax.set_xticks(np.arange(0, 301, 60))
    ax.grid(alpha=.25)
    # residual drift over the final 30 yr (271-300)
    tail = y[270:]; ft = np.isfinite(tail)
    if ft.sum() > 5:
        sl = np.polyfit(full[270:][ft], tail[ft], 1)[0]
        ax.text(0.97, 0.06, f"eq {eqm:.4g}\nfinal drift {sl:+.2g}/yr",
                transform=ax.transAxes, fontsize=8.5, va="bottom", ha="right", family="monospace",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=col, alpha=.85))

for ax in axes[1, :]:
    ax.set_xlabel("spin-up year")
axes[0, 0].text(105, axes[0, 0].get_ylim()[1], "y120\nnot archived", fontsize=7.5,
                color="0.4", ha="center", va="top")

fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print("saved:", OUT)
print(f"annual points: {np.isfinite(grid('ST_120')).sum()} / 300  (gap 91-120)")
for key, sc, title, unit, col in PAN:
    y = d[key] * sc
    print(f"{key:<9} start {y[0]:.4g} -> end {y[-1]:.4g}")
