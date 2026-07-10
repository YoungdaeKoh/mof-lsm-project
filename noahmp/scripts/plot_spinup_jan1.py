#!/opt/homebrew/bin/python3
# Noah-MP 1deg GSWP3 static-veg (DVEG=4) spin-up convergence on FIXED Jan-01 snapshots.
#
# The model's own restarts drift Jan-01 -> Dec-25 (fixed 8760 h stride against a Gregorian
# calendar), so their series carries a moving seasonal phase. These points instead come from
# jan1_snap/, where each drifted restart was integrated the remaining 1-7 days to the next
# Jan-01. That puts every point on the same calendar date, and on the same date LM4 samples.
#
# Drift = same-date difference between cycle 1 and cycle 2 at Jan-01 2010. Means are
# cos(lat)-weighted; ice-sheet columns are shown separately because offline Noah-MP has no
# glacier dynamics and they pile to the 5000 mm SNEQV cap forever.
import numpy as np
import matplotlib.pyplot as plt

CSV = "/Volumes/data01/MOF_LSM_project/noahmp/data/spinup_jan1_cyc12.csv"
OUT = "/Volumes/data01/MOF_LSM_project/figures/noahmp_spinup_convergence_jan1.png"

d = np.genfromtxt(CSV, delimiter=",", names=True)
sy, cyc, yr = d["spinyear"], d["cycle"], d["year"]
Tn, Wn = d["deepT_noice"], d["colw_noice"]
swe_ice, capped = d["swe_ice"], d["capped_ice"]
N_ICE = 7477

RED, BLU, GRY, ORA = "#c0392b", "#2471a3", "#7f8c8d", "#d35400"
i1 = np.where(cyc == 1)[0][-1]          # cycle-1 Jan-01 2010
BOUND = sy[i1] + 0.5

fig, ax = plt.subplots(1, 4, figsize=(19, 4.3))
fig.suptitle(
    "Noah-MP offline spin-up convergence  (GSWP3 1deg/3h, static veg DVEG=4)  "
    "1981–2010 × 2 cycles,  1° global,  cos(lat)-weighted,  Jan-01 snapshots",
    fontsize=12.5, fontweight="bold")
fig.text(0.5, 0.005,
         "every point is a true Jan-01 state (drifted restarts integrated forward 1–7 d), "
         "so the seasonal phase is fixed and directly comparable to LM4's Jan-01 restarts.",
         ha="center", fontsize=8, color="#555555")
for a in ax:
    a.axvline(BOUND, color="k", lw=1.0, ls="--", alpha=.55)
    a.grid(alpha=.3)
    a.set_xlabel("spin-up year")

ax[0].plot(sy, Tn, "o-", color=RED, ms=3.5, lw=1.6)
ax[0].set_title("Deep soil T, non-ice land (layer 4, ~1–2 m)", fontsize=10.5)
ax[0].set_ylabel("land-mean deep T (K)")
ax[0].annotate(f"{Tn[0]:.2f} K", (sy[0], Tn[0]), textcoords="offset points", xytext=(6, 2), fontsize=9)
ax[0].annotate(f"{Tn[-1]:.2f} K", (sy[-1], Tn[-1]), textcoords="offset points", xytext=(-48, 6), fontsize=9)

ax[1].plot(sy, Wn, "s-", color=BLU, ms=3.5, lw=1.6)
ax[1].set_title("Column soil water, non-ice land (4 layers)", fontsize=10.5)
ax[1].set_ylabel("land-mean column water (kg m$^{-2}$)")
ax[1].annotate(f"{Wn[0]:.0f}", (sy[0], Wn[0]), textcoords="offset points", xytext=(6, -2), fontsize=9)
ax[1].annotate(f"{Wn[-1]:.0f} kg m$^{{-2}}$", (sy[-1], Wn[-1]), textcoords="offset points",
               xytext=(-64, 6), fontsize=9)

# same-date drift: cycle-1 Jan-01 2010 vs cycle-2 Jan-01 2010
dT, dW = np.abs(np.diff(Tn)), np.abs(np.diff(Wn))
drift_T, drift_W = abs(Tn[-1] - Tn[i1]), abs(Wn[-1] - Wn[i1])
ax[2].semilogy(sy[1:], dT, "o-", color=RED, ms=2.8, lw=1.0, alpha=.6,
               label="|Δ deep T| year-to-year (K)")
ax[2].semilogy(sy[1:], dW, "s-", color=BLU, ms=2.8, lw=1.0, alpha=.6,
               label="|Δ col water| year-to-year (kg m$^{-2}$)")
ax[2].axhline(drift_T, color=RED, lw=2.0, ls=":")
ax[2].axhline(drift_W, color=BLU, lw=2.0, ls=":")
ax[2].set_ylim(max(1e-8, min(1e-6, drift_T * 0.4)), 60)
bb = dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=.85)
fT = f"{drift_T:.2e}" if drift_T < 1e-3 else f"{drift_T:.4f}"
ax[2].text(0.97, 0.055, f"cycle-to-cycle drift @ Jan-01 2010, deep T = {fT} K",
           transform=ax[2].transAxes, ha="right", fontsize=8.5, color=RED, bbox=bb)
ax[2].text(0.97, 0.145, f"cycle-to-cycle drift @ Jan-01 2010, col water = {drift_W:.2f} kg m$^{{-2}}$",
           transform=ax[2].transAxes, ha="right", fontsize=8.5, color=BLU, bbox=bb)
ax[2].set_title("Interannual noise ≫ true drift", fontsize=10.5)
ax[2].set_ylabel("magnitude (log)")
ax[2].legend(fontsize=8, loc="upper left", framealpha=.9)

ax[3].plot(sy, swe_ice, "^-", color=GRY, ms=3.5, lw=1.6, label="ice-sheet mean SWE")
ax[3].axhline(5000, color="k", lw=1.2, ls="-.", alpha=.7)
ax[3].text(1.5, 5000 * 0.955, "SNEQV cap 5000 mm", fontsize=8, color="k", alpha=.75)
ax[3].set_title(f"Ice sheet (IGBP 15, n={N_ICE}): no equilibrium", fontsize=10.5)
ax[3].set_ylabel("mean SWE (mm)", color=GRY)
ax[3].tick_params(axis="y", labelcolor=GRY)
ax[3].set_ylim(0, 5600)
ax[3].legend(fontsize=8, loc="center right")
t3 = ax[3].twinx()
t3.plot(sy, 100 * capped / N_ICE, "-", color=ORA, lw=1.6)
t3.set_ylabel("% of ice cells at cap", color=ORA, fontsize=9)
t3.tick_params(axis="y", labelcolor=ORA, labelsize=8)
t3.set_ylim(0, 100)

for a in ax:
    a.text(BOUND + 0.9, a.get_ylim()[0], " cycle 2", fontsize=8, color="k", alpha=.55, va="bottom")

fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print("saved:", OUT)
print(f"cycle-1 Jan-01 2010 : deep T {Tn[i1]:.6f} K  col water {Wn[i1]:.4f} kg/m2  ({int(yr[i1])})")
print(f"cycle-2 Jan-01 2010 : deep T {Tn[-1]:.6f} K  col water {Wn[-1]:.4f} kg/m2  ({int(yr[-1])})")
print(f"same-date drift     : deep T {drift_T:.3e} K  col water {drift_W:.4f} kg/m2")
print(f"yr-to-yr noise (last 5): deep T {dT[-5:].mean():.4f} K  col water {dW[-5:].mean():.4f} kg/m2")
