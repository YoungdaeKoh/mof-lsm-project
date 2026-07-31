"""Porting status of the four land models, shown through their spin-up records.

Three of the four have a convergence trajectory to show; JULES does not.  Its
MPI build is still unresolved and the serial build runs at 81 minutes per model
month, so the global 0.5-degree run exists as a single month - enough to prove
the port produces sensible fields, not enough for a curve.  The fourth panel
therefore reports simulated length rather than pretending otherwise.

Absolute values are NOT comparable between panels: soil depth, the definition of
column water and the land mask all differ by model (see the landmean
comparability note).  Each panel is about whether that model's own trajectory
has flattened.

Inputs : lm4/data/lm4_spinup_300yr_annual.csv
         cesm/clm_output/clm5_spinup_SPstability.csv
         noahmp/data/spinup_cyc12.csv
         jules/jules_1981_monthly.csv
Output : figures/porting_status_spinup.png
"""
import numpy as np
import matplotlib.pyplot as plt

lm4 = np.genfromtxt("lm4/data/lm4_spinup_300yr_annual.csv", delimiter=",", names=True)
clm = np.genfromtxt("cesm/clm_output/clm5_spinup_SPstability.csv", delimiter=",", names=True)
nmp = np.genfromtxt("noahmp/data/spinup_cyc12.csv", delimiter=",", names=True)
jul = np.genfromtxt("jules/jules_1981_monthly.csv", delimiter=",", names=True)

fig, axes = plt.subplots(2, 2, figsize=(15, 9))

# --- LM4+ ---------------------------------------------------------------
ax = axes[0, 0]
y, v = lm4["year"], lm4["colwater"]
ax.plot(y, v, "-", color="#08519c", lw=2)
d = np.polyfit(y[y > y.max() - 30], v[y > y.max() - 30], 1)[0]
ax.set_title("(a) LM4+  —  static vegetation, GSWP3, %d years\n"
             "column soil water   last-30-yr drift %+.3f kg m$^{-2}$ yr$^{-1}$"
             % (y.max(), d), fontsize=13, loc="left")
ax.set_ylabel("column soil water [kg/m$^2$]", fontsize=11)
ax.set_xlabel("spin-up year", fontsize=11)

# --- CLM5 ---------------------------------------------------------------
ax = axes[0, 1]
x = np.arange(clm["TWS"].size)
ax.plot(x, clm["TWS"], "-o", color="#238b45", lw=1.8, ms=3)
d = np.polyfit(x[-20:], clm["TWS"][-20:], 1)[0]
ax.set_title("(b) CLM5  —  satellite-phenology spin-up, WFDE5, %d years\n"
             "total water storage   last-20-yr drift %+.2f mm yr$^{-1}$"
             % (x.size, d), fontsize=13, loc="left")
ax.set_ylabel("TWS [mm]", fontsize=11)
ax.set_xlabel("spin-up year", fontsize=11)

# --- Noah-MP ------------------------------------------------------------
ax = axes[1, 0]
x = np.arange(nmp["colw_noice"].size)
ax.plot(x, nmp["colw_noice"], "-", color="#d95f02", lw=2)
nc1 = int((nmp["cycle"] == 1).sum())
ax.axvline(nc1 - 0.5, color="0.4", ls="--", lw=1.4)
ax.text(nc1 - 0.5, ax.get_ylim()[1], " cycle 2 ", va="top", fontsize=10, color="0.3")
c1 = nmp["colw_noice"][nmp["cycle"] == 1]
c2 = nmp["colw_noice"][nmp["cycle"] == 2]
n = min(c1.size, c2.size)
ax.set_title("(c) Noah-MP  —  static vegetation, GSWP3, %d years (2 cycles)\n"
             "column water, non-ice land   cycle-to-cycle drift %+.3f kg/m$^2$"
             % (x.size, np.mean(c2[:n] - c1[:n])), fontsize=13, loc="left")
ax.set_ylabel("column water [kg/m$^2$]", fontsize=11)
ax.set_xlabel("spin-up year", fontsize=11)

# --- how far each model has actually been run ---------------------------
ax = axes[1, 1]
labels = ["JULES\n(global, serial)", "Noah-MP\nstatic", "CLM5\nSP + BGC-AD",
          "LM4+\nstatic + dynamic"]
years = [1 / 12.0, 60, 30 + 93, 300 + 16]
colors = ["#999999", "#d95f02", "#238b45", "#08519c"]
b = ax.barh(labels, years, color=colors)
ax.set_xscale("log")
ax.set_xlim(0.05, 1000)
for rect, v in zip(b, years):
    ax.text(v * 1.15, rect.get_y() + rect.get_height() / 2,
            ("%.0f yr" % v) if v >= 1 else "1 month",
            va="center", fontsize=11)
ax.set_xlabel("simulated years completed (log scale)", fontsize=11)
ax.set_title("(d) how far each port has been run\n"
             "JULES runs globally but at 81 min per model month (MPI unresolved)",
             fontsize=13, loc="left")

for ax in axes.ravel():
    ax.grid(alpha=0.3, lw=0.5)
    ax.tick_params(labelsize=10)
fig.suptitle("Land model porting status — offline spin-up records\n"
             "absolute values are not comparable between panels "
             "(soil depth, column definition and land mask differ by model)",
             fontsize=15)
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig("figures/porting_status_spinup.png", dpi=140)
print("wrote figures/porting_status_spinup.png")
