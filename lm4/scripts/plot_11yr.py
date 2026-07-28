"""LM4 spin-up trajectory 1981-1992 (monthly) with annual-mean overlay."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

d = np.genfromtxt("monthly_11yr.csv", delimiter=",", names=True)
yr = d["year"]
uyears = np.unique(np.floor(yr)).astype(int)

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
    ax.plot(yr, d[k] * sc, "-", color="#9ecae1", lw=0.8, label="monthly")
    ax.plot(uyears + 0.5, annual(d[k]) * sc, "-o", color="#08519c", ms=4,
            lw=1.6, label="annual mean")
    ax.set_title(label, fontsize=11)
    ax.set_ylabel(unit, fontsize=9)
    ax.grid(alpha=0.3)
    ax.set_xlim(1981, 1993)
    ax.set_xticks(range(1981, 1993, 2))
axes[0, 0].legend(fontsize=8, loc="lower right")
for ax in axes[-1]:
    ax.set_xlabel("model year", fontsize=9)

fig.suptitle("LM4 offline spin-up trajectory 1981-1992 (WFDE5, C96, 24 PE)",
             fontsize=13, y=0.995)
fig.tight_layout(rect=[0, 0, 1, 0.98])
fig.savefig("lm4_spinup_11yr.png", dpi=125)
print("wrote lm4_spinup_11yr.png")
