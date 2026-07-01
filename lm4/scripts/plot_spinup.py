#!/opt/homebrew/bin/python3
# LM4 30yr static-veg GSWP3 spin-up convergence (job 2865, clamp build).
import numpy as np
import matplotlib.pyplot as plt

yr, T, W = [], [], []
for line in open("/tmp/lm4_equil_data.txt"):
    p = line.split()
    if len(p) < 3:
        continue
    yr.append(int(p[0])); T.append(float(p[1])); W.append(float(p[2]))
yr = np.array(yr); T = np.array(T); W = np.array(W)
dT = np.abs(np.diff(T)); dW = np.abs(np.diff(W))

fig, ax = plt.subplots(1, 3, figsize=(13.5, 4.0))
fig.suptitle("LM4 offline spin-up convergence  (GSWP3 cycle, static veg, qscomp-clamp)  1981–2010, C96",
             fontsize=12, fontweight="bold")

ax[0].plot(yr, T, "o-", color="#c0392b", ms=4, lw=1.6)
ax[0].set_title("Deep soil temperature", fontsize=11)
ax[0].set_xlabel("year"); ax[0].set_ylabel("land-mean deep T (K)")
ax[0].annotate(f"{T[0]:.2f} K", (yr[0], T[0]), textcoords="offset points", xytext=(6, 4), fontsize=9)
ax[0].annotate(f"{T[-1]:.2f} K", (yr[-1], T[-1]), textcoords="offset points", xytext=(-44, 6), fontsize=9)
ax[0].grid(alpha=.3)

ax[1].plot(yr, W, "s-", color="#2471a3", ms=4, lw=1.6)
ax[1].set_title("Column soil water (liquid+ice)", fontsize=11)
ax[1].set_xlabel("year"); ax[1].set_ylabel("land-mean column water (kg m$^{-2}$)")
ax[1].grid(alpha=.3)

ax[2].semilogy(yr[1:], dT, "o-", color="#c0392b", ms=4, lw=1.5, label="|Δ deep T| (K yr$^{-1}$)")
ax[2].semilogy(yr[1:], dW, "s-", color="#2471a3", ms=4, lw=1.5, label="|Δ col water| (kg m$^{-2}$ yr$^{-1}$)")
ax[2].set_title("Annual change → 0  (equilibration)", fontsize=11)
ax[2].set_xlabel("year"); ax[2].set_ylabel("|annual change| (log)")
ax[2].legend(fontsize=8.5, loc="upper right"); ax[2].grid(alpha=.3, which="both")
ax[2].annotate(f"final: {dT[-1]:.3f} K/yr", (yr[-1], dT[-1]), textcoords="offset points",
               xytext=(-78, -14), fontsize=8.5, color="#c0392b")

fig.tight_layout(rect=[0, 0, 1, 0.95])
out = "/Volumes/data01/MOF_LSM_project/figures/lm4_spinup_convergence.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
print("saved:", out)
