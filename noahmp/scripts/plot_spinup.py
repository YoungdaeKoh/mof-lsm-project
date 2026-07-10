#!/opt/homebrew/bin/python3
# Noah-MP 1deg GSWP3 static-veg (DVEG=4) spin-up convergence, cycles 1-2 (61 model years).
# Mirrors lm4/scripts/plot_spinup.py, with two additions the LM4 figure did not need:
#   1. ice-sheet columns (IGBP 15) are shown separately. Offline Noah-MP has no ice
#      dynamics, so they pile to the 5000 mm SNEQV cap and never equilibrate; folding
#      them into the land mean hides the convergence of ordinary land.
#   2. the drift panel contrasts |annual change| against the same-date cycle-to-cycle
#      difference. Both cycles replay identical GSWP3 forcing, so only that difference
#      isolates secular drift; |annual change| is dominated by forcing variability.
# Means are cos(lat) AREA-WEIGHTED (see extract_spinup_cyc12.py). Unweighted, the 1-deg
# grid over-weights the poles: non-ice deep T reads 285.53 K instead of 288.89 K and SWE
# 34.5 mm instead of 22.5 mm, which is not comparable to LM4's equal-area cubed sphere.
# Sampling date is NOT fixed: RESTART_FREQUENCY_HOURS=8760 walks it Jan-01 -> Dec-25 over
# a cycle, so the within-cycle curve carries a <=7-day seasonal wobble. The drift numbers
# compare 2010-12-25 to 2010-12-25 and are unaffected. LM4 samples Jan-01 every year.
import numpy as np
import matplotlib.pyplot as plt

CSV = "/Volumes/data01/MOF_LSM_project/noahmp/data/spinup_cyc12.csv"
OUT = "/Volumes/data01/MOF_LSM_project/figures/noahmp_spinup_convergence_2cyc.png"

d = np.genfromtxt(CSV, delimiter=",", names=True)
sy, cyc = d["spinyear"], d["cycle"]
Tn, Wn = d["deepT_noice"], d["colw_noice"]
swe_ice, capped, n_ice = d["swe_ice"], d["capped_ice"], d["n_ice"][0]

RED, BLU, GRY, ORA = "#c0392b", "#2471a3", "#7f8c8d", "#d35400"
i1 = np.where(cyc == 1)[0][-1]      # cycle-1 end (2010-12-25)
BOUND = sy[i1]

fig, ax = plt.subplots(1, 4, figsize=(19, 4.3))
fig.suptitle(
    "Noah-MP offline spin-up convergence  (GSWP3 1deg/3h, static veg DVEG=4)  "
    "1981–2010 × 2 cycles,  1° global,  cos(lat)-weighted",
    fontsize=12.5, fontweight="bold")
fig.text(0.5, 0.005,
         "restart sampling walks Jan-01 → Dec-25 within a cycle (8760 h stride); "
         "drift figures compare 2010-12-25 to 2010-12-25.  LM4 counterpart samples Jan-01 fixed.",
         ha="center", fontsize=8, color="#555555")
for a in ax:
    a.axvline(BOUND, color="k", lw=1.0, ls="--", alpha=.55)
    a.grid(alpha=.3)
    a.set_xlabel("spin-up year")

# --- panel 1: deep soil temperature, non-ice land -----------------------------------
ax[0].plot(sy, Tn, "o-", color=RED, ms=3.5, lw=1.6)
ax[0].set_title("Deep soil T, non-ice land (layer 4, ~1–2 m)", fontsize=10.5)
ax[0].set_ylabel("land-mean deep T (K)")
ax[0].annotate(f"{Tn[0]:.2f} K", (sy[0], Tn[0]), textcoords="offset points", xytext=(6, 2), fontsize=9)
ax[0].annotate(f"{Tn[-1]:.2f} K", (sy[-1], Tn[-1]), textcoords="offset points", xytext=(-48, 6), fontsize=9)

# --- panel 2: column soil water, non-ice land ---------------------------------------
ax[1].plot(sy, Wn, "s-", color=BLU, ms=3.5, lw=1.6)
ax[1].set_title("Column soil water, non-ice land (4 layers)", fontsize=10.5)
ax[1].set_ylabel("land-mean column water (kg m$^{-2}$)")
ax[1].annotate(f"{Wn[0]:.0f}", (sy[0], Wn[0]), textcoords="offset points", xytext=(6, -2), fontsize=9)
ax[1].annotate(f"{Wn[-1]:.0f} kg m$^{{-2}}$", (sy[-1], Wn[-1]), textcoords="offset points",
               xytext=(-64, 6), fontsize=9)

# --- panel 3: interannual noise vs true drift ---------------------------------------
dT, dW = np.abs(np.diff(Tn)), np.abs(np.diff(Wn))
drift_T, drift_W = abs(Tn[-1] - Tn[i1]), abs(Wn[-1] - Wn[i1])
ax[2].semilogy(sy[1:], dT, "o-", color=RED, ms=2.8, lw=1.0, alpha=.55,
               label="|Δ deep T| year-to-year (K)")
ax[2].semilogy(sy[1:], dW, "s-", color=BLU, ms=2.8, lw=1.0, alpha=.55,
               label="|Δ col water| year-to-year (kg m$^{-2}$)")
ax[2].axhline(drift_T, color=RED, lw=2.0, ls=":")
ax[2].axhline(drift_W, color=BLU, lw=2.0, ls=":")
ax[2].set_ylim(max(1e-8, min(1e-6, drift_T * 0.4)), 60)
bb = dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=.85)
fmt_T = f"{drift_T:.2e}" if drift_T < 1e-3 else f"{drift_T:.4f}"
ax[2].text(0.97, 0.055, f"cycle-to-cycle drift, deep T = {fmt_T} K",
           transform=ax[2].transAxes, ha="right", fontsize=8.5, color=RED, bbox=bb)
ax[2].text(0.97, 0.145, f"cycle-to-cycle drift, col water = {drift_W:.2f} kg m$^{{-2}}$",
           transform=ax[2].transAxes, ha="right", fontsize=8.5, color=BLU, bbox=bb)
ax[2].set_title("Interannual noise ≫ true drift", fontsize=10.5)
ax[2].set_ylabel("magnitude (log)")
ax[2].legend(fontsize=8, loc="upper left", framealpha=.9)

# --- panel 4: the part that never equilibrates --------------------------------------
ax[3].plot(sy, swe_ice, "^-", color=GRY, ms=3.5, lw=1.6, label="ice-sheet mean SWE")
ax[3].axhline(5000, color="k", lw=1.2, ls="-.", alpha=.7)
ax[3].text(1.5, 5000 * 0.955, "SNEQV cap 5000 mm", fontsize=8, color="k", alpha=.75)
ax[3].set_title(f"Ice sheet (IGBP 15, n={int(n_ice)}): no equilibrium", fontsize=10.5)
ax[3].set_ylabel("mean SWE (mm)", color=GRY)
ax[3].tick_params(axis="y", labelcolor=GRY)
ax[3].set_ylim(0, 5600)
ax[3].legend(fontsize=8, loc="lower right")
t3 = ax[3].twinx()
t3.plot(sy, 100 * capped / n_ice, "-", color=ORA, lw=1.6)
t3.set_ylabel("% of ice cells at cap", color=ORA, fontsize=9)
t3.tick_params(axis="y", labelcolor=ORA, labelsize=8)
t3.set_ylim(0, 100)

for a in ax:
    a.text(BOUND + 0.9, a.get_ylim()[0], " cycle 2", fontsize=8, color="k", alpha=.55, va="bottom")

fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print("saved:", OUT)
print(f"non-ice drift per 30-yr cycle : deep T {drift_T:.6f} K   col water {drift_W:.4f} kg m-2")
print(f"year-to-year noise (last 5)   : deep T {dT[-5:].mean():.4f} K   col water {dW[-5:].mean():.4f} kg m-2")
print(f"ice SWE {swe_ice[0]:.0f} -> {swe_ice[-1]:.0f} mm ; capped {int(capped[0])} -> {int(capped[-1])} / {int(n_ice)}")
