#!/opt/homebrew/bin/python3
# LM4 WFDE5 dynamic-veg CONTINUOUS spin-up (300 yr) — JJA (Jun-Jul-Aug) unweighted
# global-land mean time series. Forcing loops 1981-2010 every 30 yr (marked).
# Convergence tracked by last-30yr linear slope per panel.
import numpy as np
import matplotlib.pyplot as plt

CSV = "/Volumes/data01/MOF_LSM_project/lm4/data/jja_spinup_cont.csv"
OUT = "/Volumes/data01/MOF_LSM_project/figures/lm4_jja_cont_spinup.png"

d = np.genfromtxt(CSV, delimiter=",", names=True)
y = d["spinup_year"]

PAN = [
    ("btot",       1.0,  "Vegetation carbon (btot)",        "kg C m$^{-2}$", "#3a7a37"),
    ("soilC",      1.0,  "Soil carbon (fast+slow, column)", "kg C m$^{-2}$", "#6b4423"),
    ("colwater",   1.0,  "Column soil water (liq+ice)",     "kg m$^{-2}$",   "#1f6f8b"),
    ("soilT_deep", 1.0,  "Soil temperature (~2 m)",         "K",             "#b5551a"),
    ("LAI",        1.0,  "LAI",                             "m$^2$ m$^{-2}$","#4a8c2a"),
    ("nep",        1.0,  "NEP (→0 at equilibrium)",     "kg C m$^{-2}$", "#8a3a8a"),
    ("sens",       1.0,  "Sensible heat (JJA)",             "W m$^{-2}$",    "#c0392b"),
    ("evap",       1e3,  "Evaporation (JJA)",               "g m$^{-2}$ s$^{-1}$", "#2874a6"),
]

wrap = np.arange(1, int(y.max()) + 1, 30)   # forcing loop-back years (≡1 mod 30)

fig, axes = plt.subplots(4, 2, figsize=(13, 11))
fig.suptitle("LM4 WFDE5 dynamic-veg CONTINUOUS spin-up (300 yr) — JJA global-land mean "
             "(forcing loops 1981-2010 every 30 yr)",
             fontsize=12.5, fontweight="bold")

for ax, (key, sc, title, unit, col) in zip(axes.flat, PAN):
    v = d[key] * sc
    for w in wrap:
        ax.axvline(w, color="0.8", ls=":", lw=0.7, zorder=1)
    ax.plot(y, v, "-", color=col, lw=1.2, zorder=3)
    # last-30yr convergence slope
    m = y > y.max() - 30
    sl = np.polyfit(y[m], v[m], 1)[0]
    ax.set_title(title, fontsize=10.5)
    ax.set_ylabel(unit, fontsize=9)
    ax.grid(alpha=.25)
    conv = "converged" if abs(sl) < 0.01 * (abs(np.nanmean(v)) + 1e-9) else "still drifting"
    ax.text(0.97, 0.06, f"last-30yr slope={sl:+.3g}/yr\n{conv}",
            transform=ax.transAxes, fontsize=8, va="bottom", ha="right",
            family="monospace",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=col, alpha=.85))

for ax in axes[-1, :]:
    ax.set_xlabel("cumulative spin-up year")

fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print("saved:", OUT)
print("\n=== last-30yr slope (convergence) ===")
for key, sc, title, unit, col in PAN:
    v = d[key] * sc
    m = y > y.max() - 30
    sl = np.polyfit(y[m], v[m], 1)[0]
    print(f"{key:<11} y1={v[0]:.4g} y300={v[-1]:.4g}  slope={sl:+.3g}/yr")
