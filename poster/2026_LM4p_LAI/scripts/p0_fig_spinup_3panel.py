#!/usr/bin/env python3
"""Poster Fig. 0 (panel 1): LM4p spin-up, condensed to LAI / GPP / wood carbon.

Same data and annual averaging as analysis/plot_spinup_4models.py lm4p():
  lm4/data/monthly_noice_30yr.csv           cycle 1 = spin-up, WFDE5 1981-2010 after the KIOST 400-yr IC
  lm4/data/monthly_noice_ctl_1981_2010.csv  cycle 2 = ctl production run 1981-2010
  non-ice land mean (C96, extract_monthly_noice.py); annual = Jan-Nov mean (Dec missing 1991-96, notes 13.45)
output: ../figures/fig0_spinup_lai_gpp_wood.png, ../data/spinup_cycle_drift.txt
Drift = same forcing year, cycle 2 minus cycle 1 (last year, 2010).
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = "../../../lm4/data/"
RUN = 11      # running-mean window, years
YPAD = 0.10   # y axis = 60-yr mean +- 10 % in every panel, so flat and drifting variables compare fairly
parts = []
for f in ("monthly_noice_30yr.csv", "monthly_noice_ctl_1981_2010.csv"):
    m = pd.read_csv(R + f)
    m = m[m.month <= 11]
    parts.append(m.groupby("year").mean(numeric_only=True).reset_index())
n1 = len(parts[0])
d = pd.concat(parts, ignore_index=True)
x = np.arange(1, len(d) + 1)
series = [("LAI", d.LAI.values, "m$^2$ m$^{-2}$"),
          ("GPP", d.GPP.values * 1000 / 365, "gC m$^{-2}$ d$^{-1}$"),
          ("Wood carbon", d.bwood.values, "kgC m$^{-2}$")]

out = ["LM4p spin-up drift: cycle 2 (ctl 1981-2010) minus cycle 1 (spin-up 1981-2010), same forcing year; non-ice land mean, Jan-Nov annual mean",
       "years per cycle: %d + %d" % (n1, len(d) - n1), ""]
fig, axs = plt.subplots(1, 3, figsize=(12, 3.4))
for ax, (name, y, unit) in zip(axs, series):
    c1, c2 = y[:n1], y[n1:]
    last = (c2[-1] / c1[-1] - 1) * 100
    mean = (c2.mean() / c1.mean() - 1) * 100
    out.append("%-12s last year (2010): c1 %.4f c2 %.4f diff %+.2f %% | 30-yr mean: c1 %.4f c2 %.4f diff %+.2f %%"
               % (name, c1[-1], c2[-1], last, c1.mean(), c2.mean(), mean))
    print(out[-1])
    ax.axvspan(n1 + 1.5, len(d) + 0.5, color="0.92", lw=0)   # analysis period 1982-2010
    ax.axvline(n1 + 0.5, color="0.3", ls="--", lw=1)
    ax.plot(x, y, color="#1baf7a", lw=1.2, alpha=0.6, label="annual")
    k = RUN // 2   # centred running mean, full windows only (no edge padding)
    ax.plot(x[k:-k], np.convolve(y, np.ones(RUN) / RUN, mode="valid"), color="#0b6b48", lw=2.5,
            label="%d-yr running mean" % RUN)
    ax.set_ylim(y.mean() * (1 - YPAD), y.mean() * (1 + YPAD))   # same relative range in every panel
    ax.set_title(("%s  (cycle 2 − cycle 1: %+.1f %%)" % (name, last)).replace("-", "−"), fontsize=10, loc="left")
    ax.set_ylabel(unit)
    ax.set_xlabel("spin-up year")
    ax.set_xlim(0, len(d) + 1)
    ax.grid(alpha=0.3)
axs[0].text(0.25, 0.04, "cycle 1\nspin-up", transform=axs[0].transAxes, ha="center", fontsize=9, color="0.3")
axs[0].text(0.75, 0.04, "cycle 2 = ctl\nanalysis 1982–2010", transform=axs[0].transAxes, ha="center", fontsize=9, color="0.3")
axs[0].legend(loc="upper right", fontsize=8.5, frameon=False)
fig.suptitle("LM4+ offline spin-up after the 400-yr coupled initial state: WFDE5 1981–2010 forcing repeated twice\n(non-ice land mean; cycle difference for forcing year 2010; y axis = 60-yr mean ± 10 % in every panel)", fontsize=9.5)
fig.tight_layout(rect=(0, 0, 1, 0.86))
fig.savefig("../figures/fig0_spinup_lai_gpp_wood.png", dpi=200)
open("../data/spinup_cycle_drift.txt", "w").write("\n".join(out) + "\n")
