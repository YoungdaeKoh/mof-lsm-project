"""Porting status of the three land models that have a spin-up trajectory.

One panel, three curves, sixty years -- which is not an arbitrary window but two
full cycles of the GSWP3 forcing.  Noah-MP and CLM5 were both driven by GSWP3
1981-2010 twice; LM4+ cycles the same forcing in thirty-year blocks, so its first
sixty years are two cycles as well.

Soil temperature rather than column water storage, because temperature is the one
state variable the models report in the same unit.  The absolute values are still
far apart -- 271, 286 and 289 K -- because the depth sampled and the land mask
differ, so each curve is drawn as a departure from its own first year.  That is
not a workaround: the question the figure answers is whether a trajectory has
flattened, and a departure answers it directly, while an absolute value only
invites a comparison that would not mean anything.

Depths are close but not identical: LM4+ 1.2 m, CLM5 1.36 m, Noah-MP its deep
layer.

The cycle boundary is drawn at year 30.  A curve that steps there is responding
to the forcing looping back, not failing to settle -- the loop-back is
discontinuous, and LM4+ shows it most because its blocks are shortest.

JULES is not drawn.  Its global 0.5-degree run exists as a single month, enough
to prove the port produces sensible fields and not enough for a curve, so it is
reported in the text.

Inputs : lm4/data/lm4_spinup_300yr_annual.csv
         cesm/clm_output/clm5_spinup_SPstability.csv
         noahmp/data/spinup_cyc12.csv
Output : figures/porting_status_spinup.png
"""
import numpy as np
import matplotlib.pyplot as plt

NYR = 60                      # two GSWP3 cycles of 1981-2010

lm4 = np.genfromtxt("lm4/data/lm4_spinup_300yr_annual.csv", delimiter=",", names=True)
clm = np.genfromtxt("cesm/clm_output/clm5_spinup_SPstability.csv", delimiter=",", names=True)
nmp = np.genfromtxt("noahmp/data/spinup_cyc12.csv", delimiter=",", names=True)

SERIES = [
    ("LM4+   1.2 m", lm4["ST_120"], "#08519c"),
    ("CLM5   1.36 m", clm["TSOI_L10"], "#238b45"),
    ("Noah-MP   deep layer", nmp["deepT_noice"], "#d95f02"),
]

fig, ax = plt.subplots(figsize=(11, 5.8))
print("%-24s %7s %10s %16s" % ("model", "years", "year 1 [K]", "drift, last 20 yr"))
for name, v, col in SERIES:
    v = np.asarray(v, dtype="f8")[:NYR]
    x = np.arange(1, v.size + 1)
    a = v - v[0]
    ax.plot(x, a, "-", color=col, lw=2.2, label=name)
    d = np.polyfit(x[-20:], a[-20:], 1)[0]
    print("%-24s %7d %10.2f %+13.4f K/yr" % (name.split("  ")[0], v.size, v[0], d))

ax.axhline(0.0, color="0.45", lw=1.0, zorder=1)
ax.axvline(30.5, color="0.5", ls="--", lw=1.3, zorder=1)
lo, hi = ax.get_ylim()
ax.text(31.2, hi, " GSWP3 cycle 2 ", va="top", fontsize=11, color="0.3")
ax.set_ylim(lo, hi)
ax.set_xlabel("spin-up year", fontsize=13)
ax.set_ylabel("soil temperature, departure from year 1  [K]", fontsize=13)
ax.set_xlim(1, NYR)
ax.tick_params(labelsize=11.5)
ax.grid(alpha=0.3, lw=0.5)
ax.legend(fontsize=12, loc="center right", framealpha=0.92)

# CLM5 cold-started and climbs 10 K, which flattens the other two against the
# axis; an inset carries their range without splitting the figure
axin = ax.inset_axes([0.085, 0.14, 0.42, 0.36])
for name, v, col in SERIES:
    if name.startswith("CLM5"):
        continue
    v = np.asarray(v, dtype="f8")[:NYR]
    axin.plot(np.arange(1, v.size + 1), v - v[0], "-", color=col, lw=1.8)
axin.axhline(0.0, color="0.45", lw=0.9)
axin.axvline(30.5, color="0.5", ls="--", lw=1.1)
axin.set_xlim(1, NYR)
axin.tick_params(labelsize=9.5)
axin.grid(alpha=0.3, lw=0.4)
axin.set_title("LM4+ and Noah-MP, enlarged", fontsize=10, loc="left", pad=3)

ax.set_title("Offline spin-up of the three ported land models — two GSWP3 cycles "
             "(1981–2010 x2)\n"
             "each curve is a departure from its own first year; sampled depth "
             "and land mask differ by model", fontsize=13, loc="left")
fig.tight_layout()
fig.savefig("figures/porting_status_spinup.png", dpi=150)
print("\nwrote figures/porting_status_spinup.png")
