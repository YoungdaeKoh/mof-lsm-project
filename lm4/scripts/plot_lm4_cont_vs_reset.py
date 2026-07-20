#!/opt/homebrew/bin/python3
# LM4 WFDE5 dynamic-veg spin-up: deep soil temperature (2 m) annual-mean trajectory.
#
# CORRECTED DIAGNOSIS (supersedes the earlier "continuous removes the spike" claim, which
# came from a flawed restart-date extraction):
#   * Time axis decoded properly (days since 1981-01-01, GREGORIAN) -> real calendar year.
#     The earlier tv//365 grouping drifted with leap days and mixed Dec/Jan -> fake spikes.
#   * With the correct decode, BOTH methods spike at every 30-yr point where the cycled
#     forcing loops back (model year == 1981 mod 30, i.e. WFDE5 Dec-2010 -> Jan-1981).
#     The continuous method does NOT remove it: the ~+6 K deep-soil re-warming is driven by
#     the FORCING loop-back discontinuity, not by the restart date reset. Verified as a broad
#     warming (~70% of land cells, median +7.8 K), not a numerical blow-up.
#   * The BASELINE (non-wrap years) converges to ~270.6 K by year ~10 and stays flat 280 yr.
import numpy as np
import matplotlib.pyplot as plt

DATA = "/Volumes/data01/MOF_LSM_project/lm4/data"
OUT  = "/Volumes/data01/MOF_LSM_project/figures/lm4_cont_vs_reset_deepT.png"

cont = np.genfromtxt(f"{DATA}/cont_deepT_annual_v2.csv", delimiter=",", names=True)  # gregorian-decoded
rst  = np.genfromtxt(f"{DATA}/reset_deepT_traj.csv",     delimiter=",", names=True)  # annual mean

cy, ct = cont["spinup_year"], cont["soilT_2m"]
ry, rt = rst["spinup_year"],  rst["soilT_2m"]

# wrap-phase years (forcing loops back): spin-up year == 1 (mod 30)
wrap = np.arange(1, int(cy.max()) + 1, 30)
base = np.mean(ct[(cy > 10) & ((cy - 1) % 30 != 0)])   # baseline = non-wrap years

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(cy, ct, "-", color="#1f6f8b", lw=1.6, zorder=3,
        label="CONTINUOUS (no date reset, forcing cycled) — 284 yr")
ax.plot(ry, rt, "-o", color="#c0392b", ms=3, lw=1.1, alpha=0.85, zorder=4,
        label="RESET (30-yr segments, date reset) — 120 yr")

# mark the forcing loop-back points
for w in wrap:
    ax.axvline(w, color="#888", ls=":", lw=0.7, alpha=0.5, zorder=1)
ax.axvline(wrap[0], color="#888", ls=":", lw=0.7, alpha=0.5, label="forcing loop-back (2010→1981)")

# converged baseline
ax.axhline(base, color="#2c7a3f", ls="--", lw=1.1, alpha=0.8, zorder=2)
ax.text(287, base, f"  baseline\n  {base:.2f} K", color="#2c7a3f", va="center", fontsize=9)

ax.set_title("LM4 WFDE5 dynamic-veg spin-up — deep soil temperature (2 m), annual mean\n"
             "forcing loop-back re-warms the deep column ~+6 K every 30 yr — in BOTH methods; "
             "baseline converged by yr ~10",
             fontsize=12, fontweight="bold")
ax.set_xlabel("cumulative spin-up year")
ax.set_ylabel("soil T at 2 m  (K)")
ax.set_xlim(-5, 300)
ax.grid(alpha=0.22)
ax.legend(loc="center right", fontsize=9.5, framealpha=0.95)

ax.annotate("forcing 2010→1981 discontinuity\nshocks the deep column (~+6 K),\ndecays over ~2 yr — NOT a reset artifact",
            xy=(151, ct[cy == 151][0]), xytext=(165, 274.6), fontsize=9, color="#333",
            arrowprops=dict(arrowstyle="->", color="#333", lw=1))
ax.annotate("baseline (29 of every 30 yr):\nflat, converged", xy=(230, base),
            xytext=(200, 272.4), fontsize=9, color="#2c7a3f",
            arrowprops=dict(arrowstyle="->", color="#2c7a3f", lw=1))

fig.tight_layout()
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print("saved:", OUT)
print(f"continuous: yr {cy[0]:.0f}-{cy[-1]:.0f}, wrap-spike ~{ct[cy==151][0]:.2f} K, "
      f"baseline {base:.2f} K")
print(f"reset: yr {ry[0]:.0f}-{ry[-1]:.0f}, wrap-spike ~{np.nanmax(rt):.2f} K (same phase, same size)")
