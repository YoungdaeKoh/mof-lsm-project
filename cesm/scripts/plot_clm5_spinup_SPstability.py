#!/opt/homebrew/bin/python3
# CLM5.0-SP spin-up stability figure in the OFFICIAL SpinupStability_SP.ncl format
# (CLM User's Guide Fig 1.5.1): the six variables the tool watches, one panel each,
# annual global land mean vs spin-up year, with a dotted equilibrium band.
#   FSH, EFLX_LH_TOT, FPSN (photosynthesis; SP has no GPP field), TWS,
#   H2OSOI layer 8 (~0.80 m), TSOI layer 10 (~1.36 m).
# Equilibrium band = mean +/- 1 sigma over the final 10 spin-up years (dotted lines),
# the "specified equilibrium state" the guide refers to. Area-weighted; Jan monthly means.
import numpy as np
import matplotlib.pyplot as plt

CSV = "/Volumes/data01/MOF_LSM_project/cesm/clm_output/clm5_spinup_SPstability.csv"
OUT = "/Volumes/data01/MOF_LSM_project/figures/clm5_spinup_SPstability.png"

d = np.genfromtxt(CSV, delimiter=",", names=True)
sy = d["spinyear"]
i1 = np.where(d["cycle"] == 1)[0][-1]
BOUND = sy[i1] + 0.5

# (key, title, units, color)
PAN = [
    ("FSH",       "FSH — sensible heat flux",       "W m$^{-2}$",       "#c0392b"),
    ("LH",        "EFLX_LH_TOT — latent heat flux", "W m$^{-2}$",       "#2471a3"),
    ("FPSN",      "FPSN — photosynthesis",          "µmol m$^{-2}$ s$^{-1}$", "#3a7a37"),
    ("TWS",       "TWS — total water storage",      "mm",               "#b5791a"),
    ("H2OSOI_L8", "H2OSOI — soil water, layer 8 (0.80 m)", "mm³ mm$^{-3}$", "#7d3c98"),
    ("TSOI_L10",  "TSOI — soil temperature, layer 10 (1.36 m)", "K",   "#117a8b"),
]

fig, axes = plt.subplots(2, 3, figsize=(15, 7.2))
fig.suptitle(
    "CLM5.0-SP spin-up stability  (GSWP3 f09, 1981–2010 × 2 cycles)  —  "
    "SpinupStability_SP variable set, area-weighted",
    fontsize=13, fontweight="bold")

for ax, (key, title, unit, col) in zip(axes.flat, PAN):
    y = d[key]
    eqm = y[-10:].mean()          # equilibrium = final-decade mean
    eqs = y[-10:].std()
    ax.axhspan(eqm - eqs, eqm + eqs, color=col, alpha=.10)
    ax.axhline(eqm, color=col, ls=":", lw=1.4)          # dotted equilibrium line (guide style)
    ax.axvline(BOUND, color="k", ls="--", lw=0.9, alpha=.5)
    ax.plot(sy, y, "-", color=col, lw=1.7, marker="o", ms=2.8)
    ax.set_title(title, fontsize=10.5)
    ax.set_ylabel(unit, fontsize=9.5)
    ax.grid(alpha=.25)
    # per-panel convergence readout: last-5yr |annual change|
    d5 = np.abs(np.diff(y))[-5:].mean()
    drift = y[-1] - y[i1]                                # same-forcing-phase cycle drift
    ax.text(0.03, 0.06,
            f"eq {eqm:.3g}\n|Δ/yr|₅ {d5:.3g}\ncyc-drift {drift:+.3g}",
            transform=ax.transAxes, fontsize=8, va="bottom", family="monospace",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=col, alpha=.85))

for ax in axes[1, :]:
    ax.set_xlabel("spin-up year")
axes[0, 0].text(BOUND + 0.6, axes[0, 0].get_ylim()[0], " cycle 2",
                fontsize=8, color="k", alpha=.5, va="bottom")

fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print("saved:", OUT)
print(f"{'var':<11}{'equilibrium':>13}{'|Δ/yr| last5':>14}{'cycle drift':>13}")
for key, title, unit, col in PAN:
    y = d[key]
    print(f"{key:<11}{y[-10:].mean():>13.4g}{np.abs(np.diff(y))[-5:].mean():>14.4g}{y[-1]-y[i1]:>+13.4g}")
