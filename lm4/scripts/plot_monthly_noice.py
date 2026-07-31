"""Monthly spin-up trajectory for LM4+ offline, ice sheets removed, December filled in.

The archive holds Jan-Nov for every year except 1990, which was re-run with
days=365 and therefore has a real December (NOTES 13.36/13.38).  That one year
is used to calibrate the gap-fill: interpolating Nov and the following January
misses the true December by a fixed offset, so the offset measured at 1990 is
added to the interpolation everywhere else.

The estimate is a stopgap.  The 1991-1996 re-runs will replace it with model
output; estimated points are drawn as open circles so they are never mistaken
for data.

Input : lm4/data/monthly_noice_16yr.csv   (soil_area>0 minus Greenland, Iceland kept)
Output: figures/lm4_monthly_noice.png, lm4/data/monthly_noice_16yr_decfilled.csv
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

CSV = "lm4/data/monthly_noice_16yr.csv"
OUT_PNG = "figures/lm4_monthly_noice.png"
OUT_CSV = "lm4/data/monthly_noice_16yr_decfilled.csv"

S = 86400.0  # kg/(m2 s) -> mm/day

PANELS = [
    ("LAI",       "LAI",               "m$^2$/m$^2$",             1.0),
    ("GPP",       "GPP",               "kg C m$^{-2}$ yr$^{-1}$", 1.0),
    ("NEP",       "NEP",               "kg C m$^{-2}$ yr$^{-1}$", 1.0),
    ("soilC",     "Total soil carbon", "kg C/m$^2$",              1.0),
    ("evap",      "Evapotranspiration", "mm/day",                 S),
    ("sens",      "Sensible heat",     "W/m$^2$",                 1.0),
    ("runoff",    "Total runoff",      "mm/day",                  S),
    ("col_water", "Column soil water", "kg/m$^2$",                1.0),
]

d = np.genfromtxt(CSV, delimiter=",", names=True)
yr = d["year"].astype(int)
mo = d["month"].astype(int)
years = np.unique(yr)

def get(key, y, m):
    s = (yr == y) & (mo == m)
    return d[key][s][0] if s.any() else np.nan

# --- December gap-fill, calibrated on the 1990 re-run -------------------------
print("December gap-fill, offset calibrated on the 1990 re-run\n")
print("%-10s %10s %10s %10s %8s" % ("var", "interp90", "true90", "offset", "rel"))
filled = {}
for key, _, _, _ in PANELS:
    i90 = 0.5 * (get(key, 1990, 11) + get(key, 1991, 1))
    t90 = get(key, 1990, 12)
    off = t90 - i90
    rel = off / abs(t90) * 100 if t90 != 0 else np.nan
    print("%-10s %10.4f %10.4f %+10.4f %7.2f%%" % (key, i90, t90, off, rel))

    dec = {}
    for y in years:
        if y == 1990:
            dec[y] = (t90, False)                       # real model output
            continue
        jan_next = get(key, y + 1, 1)
        proxy = False
        if not np.isfinite(jan_next):                   # 1996: no 1997 yet
            jan_next = get(key, y, 1)
            proxy = True
        dec[y] = (0.5 * (get(key, y, 11) + jan_next) + off, True)
        if proxy:
            dec[y] = (dec[y][0], True)
    filled[key] = dec

# --- assemble the continuous monthly series ---------------------------------
t_all, series, est_flag = [], {k: [] for k, _, _, _ in PANELS}, []
for y in years:
    for m in range(1, 13):
        t_all.append(y + (m - 0.5) / 12.0)
        est_flag.append(m == 12 and filled[PANELS[0][0]][y][1])
        for key, _, _, sc in PANELS:
            v = filled[key][y][0] if m == 12 else get(key, y, m)
            series[key].append(v * sc)
t_all = np.array(t_all)
est_flag = np.array(est_flag)
for k in series:
    series[k] = np.array(series[k])

ann = {k: np.array([series[k][(t_all > y) & (t_all < y + 1)].mean() for y in years])
       for k in series}

print("\n연평균 (12개월, 12월 = 추정치 포함), 선형추세")
print("%-10s %10s %10s %12s %12s" % ("var", "1990", "1996", "1981-96", "1990-96"))
for key, _, _, _ in PANELS:
    a = ann[key]
    t1 = np.polyfit(years, a, 1)[0] / abs(a.mean()) * 100
    s = years >= 1990
    t2 = np.polyfit(years[s], a[s], 1)[0] / abs(a[s].mean()) * 100
    print("%-10s %10.4f %10.4f %11.3f%% %11.3f%%"
          % (key, a[years == 1990][0], a[-1], t1, t2))

hdr = "year,month," + ",".join(k for k, _, _, _ in PANELS) + ",dec_estimated"
np.savetxt(OUT_CSV,
           np.column_stack([np.floor(t_all).astype(int),
                            np.round((t_all - np.floor(t_all)) * 12 + 0.5).astype(int)]
                           + [series[k] for k, _, _, _ in PANELS]
                           + [est_flag.astype(int)]),
           delimiter=",", header=hdr, comments="", fmt="%.6f")

# --- figure ------------------------------------------------------------------
fig, axes = plt.subplots(2, 4, figsize=(26, 10.5), sharex=True)
for n, (ax, (key, label, unit, _)) in enumerate(zip(axes.ravel(), PANELS)):
    v = series[key]
    a = ann[key]
    ax.plot(t_all, v, "-", color="#9ecae1", lw=1.1, zorder=2, label="monthly")
    ax.plot(years + 0.5, a, "o-", color="#08519c", ms=5.5, lw=2.2, zorder=5,
            label="annual mean")
    # trend numbers stay in the printed table, not on the panels -- they
    # collided with the curves at this font size
    ax.set_title("(%s) %s  [%s]" % ("abcdefgh"[n], label, unit),
                 fontsize=20, loc="left")
    ax.grid(alpha=0.3, lw=0.5)
    ax.tick_params(labelsize=16)
    ax.xaxis.set_major_locator(MultipleLocator(5))   # 5-year labels
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.set_xlim(years[0], years[-1] + 1)
    lo, hi = ax.get_ylim()
    if lo < 0 < hi:                                  # zero line where it matters
        ax.axhline(0.0, color="0.35", lw=2.0, zorder=1)
        ax.set_ylim(lo, hi)
axes[0, 0].legend(fontsize=14, loc="upper left", framealpha=0.9)
for ax in axes[-1]:
    ax.set_xlabel("year", fontsize=18)
fig.suptitle("LM4+ offline spin-up (WFDE5, C96, dynamic vegetation) 1981–1996 — ice sheets excluded\n"
             "17,219 non-ice land points (Antarctica, and Greenland by its outline);  "
             "December estimated except 1990 (re-run)",
             fontsize=17)
fig.tight_layout(rect=[0, 0, 1, 0.945])
fig.savefig(OUT_PNG, dpi=140)
print("\nwrote %s and %s" % (OUT_PNG, OUT_CSV))
