#!/usr/bin/env python3
"""Poster Fig. 3 (panel 4), normalised version: seasonal timing of the pilot runs, six AR6 regions.

Reads the regional monthly means written by p4_fig_phentest_regions.py (../data/phentest_regions_summary.txt)
and scales every curve to its own annual range, (LAI - min) / (max - min), so only the timing is
compared; the magnitude bias is shown in Fig. 1 instead.  GIMMS is the thick grey target line,
CTRL is black, the experiments are coloured.  Runs missing from the summary are skipped.
output: ../figures/fig3b_phentest_regions_normalised.png
"""
import re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RUNS = [("GIMMS", "GIMMS", "0.65", "-", 2.2),          # legend keeps the short run names; definitions go in the caption
        ("base", "CTRL", "k", "-", 2.2),
        ("tc10", "TC10", "tab:blue", "-.", 2.2),
        ("offon", "DL14+TC10", "tab:red", "--", 2.4),
        ("dayl", "DL13/12", "tab:green", "-", 2.0),
        ("dayl2", "DLtype", "tab:purple", "--", 2.0)]

regions, cur = [], None
import os
SUFFIX = "" if os.environ.get("REGSET", "default") == "default" else "_" + os.environ["REGSET"]   # same choice as p4
for line in open("../data/phentest_regions_summary%s.txt" % SUFFIX):
    m = re.match(r"^(\S.*\(\w{3}\))\s+\(\d+ cells\)", line)
    if m:
        cur = {"name": m.group(1)}; regions.append(cur); continue
    m = re.match(r"^\s+(GIMMS|base|tc10|offon|dayl|dayl2)\s+((?:[\d.]+\s*){12})$", line.rstrip()) if cur else None
    if m:
        cur[m.group(1)] = np.array(m.group(2).split(), float)

mon = np.arange(1, 13)
fig, axs = plt.subplots(2, 3, figsize=(15.5, 7.2), sharex=True, sharey=True)
for r, ax in zip(regions, axs.ravel()):
    for key, label, col, ls, lw in RUNS:
        if key not in r:
            continue
        y = r[key]
        ax.plot(mon, (y - y.min()) / (y.max() - y.min()), color=col, lw=lw, ls=ls, marker="o", ms=3, label=label,
                alpha=0.9 if key == "GIMMS" else 0.7, zorder=1 if key == "GIMMS" else 2)   # translucent so overlaps show
    ax.axhline(0.5, color="0.6", lw=0.8, ls=":")
    ax.set_title(r["name"], fontsize=11, loc="left")
    ax.set_xlim(1, 12); ax.set_ylim(-0.02, 1.02)
    ax.set_xticks(mon); ax.set_xticklabels(list("JFMAMJJASOND"))
    ax.grid(alpha=0.3)
for ax in axs[:, 0]:
    ax.set_ylabel("Normalized LAI")
axs[0, 0].legend(loc="upper left", fontsize=8.5, frameon=False)
fig.suptitle("Pilot runs 2010, seasonal timing only: each curve scaled to its own annual range (magnitude: Fig. 1). "
             "Grey = observed target, dotted = 50 % (EOS definition)", fontsize=10)
fig.tight_layout(rect=(0, 0, 1, 0.96))
fig.savefig("../figures/fig3b_phentest_regions_normalised%s.png" % SUFFIX, dpi=200)
print("regions", len(regions), "| runs:", [k for k in regions[0] if k != "name"])
