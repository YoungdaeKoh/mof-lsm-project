#!/opt/homebrew/bin/python3
# LM4 WFDE5 dynveg spin-up convergence — JJA (Jun-Jul-Aug) area-weighted global-land
# mean time series across cumulative spin-up years (cycles 1-3 = 90 yr so far).
# Each 30-yr cycle repeats 1981-2010 WFDE5 forcing; convergence = cycle-to-cycle drift shrinks.
import numpy as np
import matplotlib.pyplot as plt

CSV = "/Volumes/data01/MOF_LSM_project/lm4/data/jja_spinup.csv"
OUT = "/Volumes/data01/MOF_LSM_project/figures/lm4_wfde5_jja_spinup.png"

d = np.genfromtxt(CSV, delimiter=",", names=True)
cy = d["cum_year"]; cyc = d["cycle"]

PAN = [
    ("btot",       1.0, "Vegetation carbon (btot)",       "kg C m$^{-2}$", "#3a7a37"),
    ("soilC",      1.0, "Soil carbon (fast+slow, column)", "kg C m$^{-2}$", "#6b4423"),
    ("colwater",   1.0, "Column soil water (liq+ice)",    "kg m$^{-2}$",   "#1f6f8b"),
    ("soilT_deep", 1.0, "Soil temperature (~2 m)",        "K",             "#b5551a"),
    ("LAI",        1.0, "LAI",                            "m$^2$ m$^{-2}$","#4a8c2a"),
    ("nep",        1.0, "NEP (→0 at equilibrium)",        "kg C m$^{-2}$", "#8a3a8a"),
    ("sens",       1.0, "Sensible heat (JJA)",            "W m$^{-2}$",    "#c0392b"),
    ("evap",       1e3, "Evaporation (JJA)",              "g m$^{-2}$ s$^{-1}$", "#2874a6"),
]

fig, axes = plt.subplots(4, 2, figsize=(13, 11))
fig.suptitle("LM4 WFDE5 dynamic-veg spin-up — JJA area-weighted global-land mean "
             "(cycles 1-3, 90 yr; each cycle = 1981-2010 WFDE5)",
             fontsize=12.5, fontweight="bold")

ncyc = int(cyc.max())
for ax, (key, sc, title, unit, col) in zip(axes.flat, PAN):
    y = d[key] * sc
    ax.plot(cy, y, "-", color=col, lw=1.3)
    ax.plot(cy, y, "o", color=col, ms=2.6)
    # cycle 경계 표시
    for c in range(1, ncyc + 1):
        x0 = cy[cyc == c]
        if len(x0):
            ax.axvline(x0[0] - 0.5, color="0.7", ls=":", lw=0.8)
    # cycle별 평균 (수렴 추적)
    for c in range(1, ncyc + 1):
        m = cyc == c
        if m.sum():
            cm = np.nanmean(y[m])
            ax.hlines(cm, cy[m].min(), cy[m].max(), color=col, ls="--", lw=1.1, alpha=.7)
    ax.set_title(title, fontsize=10.5)
    ax.set_ylabel(unit, fontsize=9)
    ax.grid(alpha=.25)
    # cycle 2→3 평균 표류 (수렴 지표)
    if ncyc >= 3:
        m2 = np.nanmean(y[cyc == 2]); m3 = np.nanmean(y[cyc == 3])
        ax.text(0.97, 0.06, f"cyc2→3 Δ={m3-m2:+.3g}",
                transform=ax.transAxes, fontsize=8, va="bottom", ha="right",
                family="monospace",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=col, alpha=.85))

for ax in axes[-1, :]:
    ax.set_xlabel("cumulative spin-up year")

fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print("saved:", OUT)
# 콘솔 수렴 요약
print("\n=== cycle별 JJA 평균 + 표류 ===")
for key, sc, title, unit, col in PAN:
    y = d[key] * sc
    cms = [np.nanmean(y[cyc == c]) for c in range(1, ncyc + 1)]
    drift = f"  cyc2→3 Δ={cms[2]-cms[1]:+.3g}" if ncyc >= 3 else ""
    print(f"{key:<11} " + " ".join(f"c{c}={cm:.4g}" for c, cm in enumerate(cms, 1)) + drift)
