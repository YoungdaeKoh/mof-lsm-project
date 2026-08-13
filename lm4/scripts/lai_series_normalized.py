"""MJJAS LAI year to year, each series normalised by its own statistics.

The model's MJJAS mean is 2.87 and the observed 2.03, so drawn on one axis the
curves sit apart and nothing about their year-to-year behaviour is legible.  The
offset is a separate result (the mean-map figure puts it at +41 %); this figure
is about what the two do over time, which needs the offset out of the way.

Two normalisations, because they answer different questions:

  (a) percent of each series' own mean.  The offset goes, the amplitude stays,
      so it still shows that the model swings wider than the observations.
  (b) standardised -- also divided by each series' own standard deviation.  Now
      amplitude is gone too and only the timing is left: do the good and bad
      years line up at all?

Both baselines are computed on 1990-2010, not on the whole record: 1982-89 is
spin-up drift (NOTES 13.46), and a mean taken across it would be pulled by the
adjustment rather than describing the model's settled state.  The drift years
are still drawn, shaded, so the departure is visible instead of hidden.

Correlations are reported raw and detrended.  Raw correlation over a period when
both series trend upward is partly the trends agreeing; detrended is the test of
whether the individual years agree.

Input : lm4/data/lai_trend_vs_gimms.csv  (written by lai_trend_vs_gimms.py)
Output: figures/lai_series_normalized.png, lm4/data/lai_series_normalized.csv
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

BASE = (1990, 2010)          # drift-free window the normalisation rests on

d = np.genfromtxt("lm4/data/lai_trend_vs_gimms.csv", delimiter=",", names=True)
yr = d["year"].astype(int)
series = {"LM4+ (model)": d["lm4_mjjas"], "GIMMS LAI4g (obs)": d["gimms_mjjas"]}
base = (yr >= BASE[0]) & (yr <= BASE[1])


def detrend(y, v):
    return v - np.polyval(np.polyfit(y, v, 1), y)


print("MJJAS LAI, baseline %d-%d\n" % BASE)
print("%-20s %8s %8s %9s %10s %9s"
      % ("series", "mean", "sd", "sd/mean", "sd(detr)", "detr/mean"))
norm = {}
for k, v in series.items():
    m = v[base].mean()
    s = v[base].std(ddof=1)
    # the raw sd of the observed series carries its greening trend, so comparing
    # raw sds compares one series' variability against another's variability
    # plus a trend.  The amplitude statement has to rest on the detrended sd.
    sd_det = detrend(yr[base], v[base]).std(ddof=2)
    norm[k] = {"pct": (v - m) / m * 100.0, "std": (v - m) / sd_det,
               "mean": m, "sd": s, "sd_det": sd_det}
    print("%-20s %8.4f %8.4f %8.2f%% %10.4f %8.2f%%"
          % (k, m, s, s / m * 100, sd_det, sd_det / m * 100))

a, b = norm["LM4+ (model)"], norm["GIMMS LAI4g (obs)"]
print("\namplitude ratio, raw       (sd/mean, model/obs): %.2f"
      % ((a["sd"] / a["mean"]) / (b["sd"] / b["mean"])))
print("amplitude ratio, detrended (sd/mean, model/obs): %.2f"
      % ((a["sd_det"] / a["mean"]) / (b["sd_det"] / b["mean"])))

for lab, sel in (("1990-2010", base), ("1982-2010", yr > 0)):
    x, y = series["LM4+ (model)"][sel], series["GIMMS LAI4g (obs)"][sel]
    r_raw = np.corrcoef(x, y)[0, 1]
    r_det = np.corrcoef(detrend(yr[sel], x), detrend(yr[sel], y))[0, 1]
    print("%-10s  r(raw) %+.3f   r(detrended) %+.3f   n=%d"
          % (lab, r_raw, r_det, sel.sum()))

hdr = "year,lm4_pct,gimms_pct,lm4_std,gimms_std"
np.savetxt("lm4/data/lai_series_normalized.csv",
           np.column_stack([yr, a["pct"], b["pct"], a["std"], b["std"]]),
           delimiter=",", header=hdr, comments="", fmt="%.6f")

# ------------------------------------------------------------------ figure ---
COL = {"LM4+ (model)": "#08519c", "GIMMS LAI4g (obs)": "#238b45"}
MRK = {"LM4+ (model)": "o", "GIMMS LAI4g (obs)": "s"}

fig, axes = plt.subplots(2, 1, figsize=(13, 8.4), sharex=True)
PANELS = [("pct", "anomaly [% of the 1990–2010 mean]",
           "(a) each series as a percentage of its own mean — "
           "the offset is gone, the amplitude is not"),
          ("std", "standardised anomaly [detrended sd]",
           "(b) also divided by its own detrended standard deviation — "
           "only the timing is left")]

for ax, (key, ylab, title) in zip(axes, PANELS):
    ax.axvspan(yr[0] - 0.5, BASE[0] - 0.5, color="0.88", zorder=0)
    ax.text(yr[0] + 0.2, ax.get_ylim()[1], " spin-up drift ", va="top",
            fontsize=10, color="0.35", zorder=1)
    ax.axhline(0.0, color="0.4", lw=1.0, zorder=1)
    for k in series:
        ax.plot(yr, norm[k][key], MRK[k] + "-", color=COL[k], lw=1.9, ms=4.5,
                label=k, zorder=3)
    ax.set_ylabel(ylab, fontsize=12)
    ax.set_title(title, fontsize=13, loc="left")
    ax.grid(alpha=0.3, lw=0.5)
    ax.xaxis.set_major_locator(MultipleLocator(5))
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.set_xlim(yr[0] - 0.5, yr[-1] + 0.5)

axes[0].legend(fontsize=11, loc="lower right", framealpha=0.9)
axes[1].set_xlabel("year", fontsize=12)

x, y = series["LM4+ (model)"][base], series["GIMMS LAI4g (obs)"][base]
fig.suptitle("MJJAS LAI, each series normalised by its own 1990–2010 statistics — "
             "common 1° cells, cos-lat weighted\n"
             "model mean %.2f vs observed %.2f;  detrended spread %.2f%% vs %.2f%% "
             "(model %.2fx);  detrended r = %+.2f over 1990–2010"
             % (a["mean"], b["mean"], a["sd_det"] / a["mean"] * 100,
                b["sd_det"] / b["mean"] * 100,
                (a["sd_det"] / a["mean"]) / (b["sd_det"] / b["mean"]),
                np.corrcoef(detrend(yr[base], x), detrend(yr[base], y))[0, 1]),
             fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig("figures/lai_series_normalized.png", dpi=140)
print("\nwrote figures/lai_series_normalized.png")
