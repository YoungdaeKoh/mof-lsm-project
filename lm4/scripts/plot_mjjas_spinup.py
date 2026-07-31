"""MJJAS-mean spin-up trajectory for the LM4+ WFDE5 offline run (1981-1995).

MJJAS is the northern-hemisphere growing season and, for the global land mean,
it contains the annual maximum (July; verified in NOTES 13.38).  It is also
untouched by the missing December of the 11-month archive, so the whole record
is usable as-is.

Input : lm4/data/monthly_15yr.csv  (native land_month, 6 tiles, unweighted)
Output: lm4/data/mjjas_15yr.csv, figures/lm4_mjjas_spinup.png
"""
import numpy as np
import matplotlib.pyplot as plt

CSV = "lm4/data/monthly_15yr.csv"
OUT_CSV = "lm4/data/mjjas_15yr.csv"
OUT_PNG = "figures/lm4_mjjas_spinup.png"

S = 86400.0  # kg/(m2 s) -> mm/day

# key: (csv column, label, unit, scale)
PANELS = [
    ("LAI",       "LAI",              "m$^2$/m$^2$",       1.0),
    ("GPP",       "GPP",              "kg C m$^{-2}$ yr$^{-1}$", 1.0),
    ("NPP",       "NPP",              "kg C m$^{-2}$ yr$^{-1}$", 1.0),
    ("evap",      "Evaporation",      "mm/day",            S),
    ("runoff",    "Total runoff",     "mm/day",            S),
    ("col_water", "Column soil water", "kg/m$^2$",         1.0),
    ("SWE",       "SWE",              "kg/m$^2$",          1.0),
    ("soilC",     "Total soil carbon", "kg C/m$^2$",       1.0),
]

d = np.genfromtxt(CSV, delimiter=",", names=True)
yr = d["year"]
y = np.floor(yr).astype(int)
mo = np.round((yr - y) * 12 + 0.5).astype(int)
mjjas = (mo >= 5) & (mo <= 9)
years = np.unique(y)

series = {}
for key, _, _, sc in PANELS:
    series[key] = np.array([d[key][mjjas & (y == k)].mean() * sc for k in years])

# --- numbers first ----------------------------------------------------------
print("MJJAS (May-Sep) land-mean, %d-%d\n" % (years[0], years[-1]))
hdr = "year  " + "".join("%12s" % k for k, _, _, _ in PANELS)
print(hdr)
for i, k in enumerate(years):
    print("%4d  " % k + "".join("%12.4f" % series[key][i] for key, _, _, _ in PANELS))

print("\n선형추세 (%/yr, 창별)")
print("%-12s %10s %10s %10s" % ("var", "1981-95", "1986-95", "1990-95"))
trends = {}
for key, _, _, _ in PANELS:
    row = []
    for w0 in (1981, 1986, 1990):
        s = years >= w0
        a = np.polyfit(years[s], series[key][s], 1)[0]
        row.append(a / np.abs(series[key][s].mean()) * 100)
    trends[key] = row
    print("%-12s %9.3f%% %9.3f%% %9.3f%%" % (key, row[0], row[1], row[2]))

np.savetxt(OUT_CSV,
           np.column_stack([years] + [series[k] for k, _, _, _ in PANELS]),
           delimiter=",", header="year," + ",".join(k for k, _, _, _ in PANELS),
           comments="", fmt="%.6f")

# --- figure -----------------------------------------------------------------
fig, axes = plt.subplots(4, 2, figsize=(11, 12), sharex=True)
for ax, (key, label, unit, _) in zip(axes.ravel(), PANELS):
    v = series[key]
    ax.axvspan(1990, years[-1] + 0.3, color="0.90", zorder=0)
    ax.plot(years, v, "o-", color="#1f77b4", ms=4, lw=1.6, zorder=3)
    ax.set_ylabel("%s [%s]" % (label, unit), fontsize=9)
    ax.grid(alpha=0.3, lw=0.5)
    ax.set_title("%s   trend 1990–95: %+.2f %%/yr" % (label, trends[key][2]),
                 fontsize=9, loc="left")
for ax in axes[-1]:
    ax.set_xlabel("year")
fig.suptitle("LM4+ offline (WFDE5, C96) — MJJAS land-mean spin-up trajectory\n"
             "shaded = diagnostic window (1990–); native land_month, 6 tiles, unweighted",
             fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(OUT_PNG, dpi=140)
print("\nwrote %s and %s" % (OUT_PNG, OUT_CSV))
