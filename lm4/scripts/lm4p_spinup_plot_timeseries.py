"""Monthly global land-mean time series, LM4 spin-up 1981-1982 (22 months)."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

d = np.genfromtxt("monthly_1981_1982.csv", delimiter=",", names=True)
m = d["month"]

# (key, label, unit, scale) -- scale converts kg/m2/s -> mm/day where useful
panels = [
    ("runoff", "Runoff", "mm/day", 86400.0),
    ("evap", "Evapotranspiration", "mm/day", 86400.0),
    ("LAI", "LAI", "m$^2$/m$^2$", 1.0),
    ("GPP", "GPP", "kg C/m$^2$/yr", 1.0),
    ("theta_sfc", "Surface soil moisture", "m$^3$/m$^3$", 1.0),
    ("col_water", "Column soil water", "kg/m$^2$", 1.0),
    ("sens", "Sensible heat", "W/m$^2$", 1.0),
    ("SWE", "Snow water equiv.", "kg/m$^2$", 1.0),
    ("soilC", "Total soil carbon", "kg C/m$^2$", 1.0),
]

fig, axes = plt.subplots(3, 3, figsize=(13, 9))
for ax, (k, label, unit, sc) in zip(axes.ravel(), panels):
    ax.plot(m, d[k] * sc, "-o", ms=3, color="#2c6fbb")
    ax.set_title(label, fontsize=11)
    ax.set_ylabel(unit, fontsize=9)
    ax.grid(alpha=0.3)
    ax.set_xlim(1, 22)
    ax.axvline(11.5, color="gray", ls="--", lw=0.8)   # 1981|1982 boundary
    ax.set_xticks([1, 6, 11, 16, 21])

for ax in axes[-1]:
    ax.set_xlabel("month (1981 → 1982, Jan missing)", fontsize=9)

fig.suptitle("LM4 offline spin-up: global land-mean monthly series (WFDE5, 1981-1982)",
             fontsize=13, y=0.99)
fig.tight_layout(rect=[0, 0, 1, 0.98])
fig.savefig("lm4_spinup_timeseries.png", dpi=130)
print("wrote lm4_spinup_timeseries.png")
