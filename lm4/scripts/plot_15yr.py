"""LM4 spin-up trajectory 1981-1995 (monthly) with annual-mean overlay.

Extends plot_11yr.py to every archived year. The vertical marker at 1990 is
where the drift stops: over 1990-1995 every variable except soil carbon has a
linear trend under 0.4%/yr, so the diagnostic window can start there rather
than at the later date implied by the 1981-1992 fit in LM4_SPINUP_NOTES 13.25.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

d = np.genfromtxt("lm4/data/monthly_15yr.csv", delimiter=",", names=True)
yr = d["year"]
uyears = np.unique(np.floor(yr)).astype(int)
EQ = 1990          # start of the equilibrated window


def annual(v):
    return np.array([np.nanmean(v[np.floor(yr) == y]) for y in uyears])


panels = [
    ("LAI", "LAI", "m$^2$/m$^2$", 1.0),
    ("runoff", "Runoff (runf, total)", "mm/day", 86400.0),
    ("evap", "Evapotranspiration", "mm/day", 86400.0),
    ("GPP", "GPP", "kg C/m$^2$/yr", 1.0),
    ("theta_sfc", "Surface soil moisture", "m$^3$/m$^3$", 1.0),
    ("col_water", "Column soil water", "kg/m$^2$", 1.0),
    ("soilC", "Total soil carbon (slow)", "kg C/m$^2$", 1.0),
    ("bwood", "Wood biomass", "kg C/m$^2$", 1.0),
    ("SWE", "Snow water equiv.", "kg/m$^2$", 1.0),
]

fig, axes = plt.subplots(3, 3, figsize=(15, 10))
for ax, (k, label, unit, sc) in zip(axes.ravel(), panels):
    a = annual(d[k]) * sc
    ax.plot(yr, d[k] * sc, "-", color="#9ecae1", lw=0.8, label="monthly")
    ax.plot(uyears + 0.5, a, "-o", color="#08519c", ms=4, lw=1.6,
            label="annual mean")
    ax.axvspan(uyears[0], EQ, color="0.90", zorder=0)
    ax.axvline(EQ, color="#d95f02", lw=1.2, ls="--")
    # trend over the equilibrated window, annotated in percent per year
    late = uyears >= EQ
    tr = np.polyfit(uyears[late], a[late], 1)[0]
    rel = 100 * tr / abs(a[late].mean())
    ax.set_title("%s   [%s]   %d- trend %+.2f%%/yr" % (label, unit, EQ, rel),
                 fontsize=10)
    ax.grid(alpha=0.3)
    ax.set_xlim(uyears[0], uyears[-1] + 1)

axes[0, 0].legend(fontsize=8, loc="lower right")
for ax in axes[2]:
    ax.set_xlabel("year")
fig.suptitle("LM4+ offline spin-up (WFDE5, dynamic vegetation) 1981-1995 — "
             "grey = drifting, dashed line = equilibrated from %d" % EQ,
             fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig("figures/lm4_spinup_15yr.png", dpi=130)
print("wrote figures/lm4_spinup_15yr.png")

print("\n%-11s %9s %9s %9s" % ("var", "1981", "1995", "%d- trend/yr" % EQ))
for k, label, unit, sc in panels:
    a = annual(d[k]) * sc
    late = uyears >= EQ
    tr = np.polyfit(uyears[late], a[late], 1)[0]
    print("%-11s %9.4g %9.4g %+9.4g  (%+.2f%%/yr)"
          % (k, a[0], a[-1], tr, 100 * tr / abs(a[late].mean())))
