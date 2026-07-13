#!/opt/homebrew/bin/python3
# CLM5.0-SP GSWP3 spin-up convergence, cycles 1-2 (60 model-yr). Mirrors
# lm4/scripts/plot_spinup.py, using the variables/layers the CLM-SP guide watches.
#
# The guide (Spinning-up-the-Satellite-Phenology-Model) says surface fluxes and shallow
# soil equilibrate in <10 yr and TWS lags. The panels show exactly that. TSOI is drawn at
# layer 10 (1.36 m, the guide layer); the 42 m bottom node is overlaid faintly to show why
# it is NOT the convergence metric -- its multi-century thermal memory never settles offline.
# Means are area-weighted (area*landfrac); January monthly-mean h0 snapshots.
import numpy as np
import matplotlib.pyplot as plt

CSV = "/Volumes/data01/MOF_LSM_project/cesm/clm_output/clm5_spinup_cyc12.csv"
OUT = "/Volumes/data01/MOF_LSM_project/figures/clm5_spinup_convergence.png"

d = np.genfromtxt(CSV, delimiter=",", names=True)
sy = d["spinyear"]
i1 = np.where(d["cycle"] == 1)[0][-1]      # cycle-1 end (spinyr 30, forcing 2010)
BOUND = sy[i1] + 0.5

RED, BLU, AMB, GRN, GRY = "#c0392b", "#2471a3", "#b5791a", "#3a7a37", "#95a5a6"

fig, ax = plt.subplots(1, 3, figsize=(14.5, 4.3))
fig.suptitle(
    "CLM5.0-SP offline spin-up convergence  (GSWP3 f09, static/satellite phenology)  "
    "1981–2010 × 2 cycles,  area-weighted",
    fontsize=12.5, fontweight="bold")
for a in ax:
    a.axvline(BOUND, color="k", lw=1.0, ls="--", alpha=.55)
    a.grid(alpha=.3)
    a.set_xlabel("spin-up year")

# --- panel 1: soil temperature ------------------------------------------------------
tL10, tbot = d["TSOI_L10"], d["TSOI_bot"]
ax[0].plot(sy, tL10, "o-", color=RED, ms=3.4, lw=1.7, label="layer 10 (1.36 m) — guide")
ax[0].plot(sy, tbot, "-", color=GRY, lw=1.3, alpha=.8, label="bottom node (42 m) — not the metric")
ax[0].set_title("Soil temperature", fontsize=11)
ax[0].set_ylabel("land-mean soil T (K)")
ax[0].annotate(f"{tL10[0]:.2f} K", (sy[0], tL10[0]), textcoords="offset points", xytext=(6, 4), fontsize=9, color=RED)
ax[0].annotate(f"{tL10[-1]:.2f} K", (sy[-1], tL10[-1]), textcoords="offset points", xytext=(-46, -12), fontsize=9, color=RED)
ax[0].text(6.5, 282.7, "42 m bottom node:\n+4.3 K/cycle, never settles\n— excluded from metric",
           fontsize=8, color=GRY, va="top")
ax[0].legend(fontsize=8, loc="lower right", framealpha=.9)

# --- panel 2: column soil water -----------------------------------------------------
cw = d["colwater"]
ax[1].plot(sy, cw, "s-", color=BLU, ms=3.4, lw=1.7)
ax[1].set_title("Column soil water (liquid + ice)", fontsize=11)
ax[1].set_ylabel("land-mean column water (kg m$^{-2}$)")
ax[1].annotate(f"{cw[0]:.0f}", (sy[0], cw[0]), textcoords="offset points", xytext=(6, -2), fontsize=9)
ax[1].annotate(f"{cw[-1]:.0f} kg m$^{{-2}}$", (sy[-1], cw[-1]), textcoords="offset points", xytext=(-70, 6), fontsize=9)

# --- panel 3: |annual change| -> 0 (equilibration) ----------------------------------
def dabs(a): return np.abs(np.diff(a))
ax[2].semilogy(sy[1:], dabs(d["LH"]),       "-",  color=GRN, lw=1.4, label="|Δ latent heat| (W m$^{-2}$)")
ax[2].semilogy(sy[1:], dabs(tL10),          "o-", color=RED, ms=2.8, lw=1.3, label="|Δ soil T, 1.36 m| (K)")
ax[2].semilogy(sy[1:], dabs(cw),            "s-", color=BLU, ms=2.8, lw=1.3, label="|Δ column water| (kg m$^{-2}$)")
ax[2].semilogy(sy[1:], dabs(d["TWS"]),      "^-", color=AMB, ms=3.0, lw=1.5, label="|Δ total water storage| (mm)")
ax[2].set_title("Annual change → 0  (equilibration)", fontsize=11)
ax[2].set_ylabel("|annual change| (log)")
ax[2].legend(fontsize=7.8, loc="upper right", framealpha=.92)
# annotate the guide's message: fluxes/shallow settle, TWS lags
ax[2].annotate("TWS lags — the guide says so",
               (sy[-1], dabs(d["TWS"])[-1]), textcoords="offset points", xytext=(-140, 10), fontsize=8, color=AMB)

for a in ax:
    a.text(BOUND + 0.7, a.get_ylim()[0], " cycle 2", fontsize=8, color="k", alpha=.55, va="bottom")

fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print("saved:", OUT)
print(f"cycle-to-cycle drift (spinyr30 vs 60, same forcing phase):")
print(f"  soil T 1.36 m : {tL10[-1]-tL10[i1]:+.3f} K   column water : {cw[-1]-cw[i1]:+.1f} kg/m2   TWS : {d['TWS'][-1]-d['TWS'][i1]:+.0f} mm")
print(f"  latent heat   : {d['LH'][-1]-d['LH'][i1]:+.3f} W/m2   H2OSOI 0.8 m : {d['H2OSOI_L8'][-1]-d['H2OSOI_L8'][i1]:+.4f}")
