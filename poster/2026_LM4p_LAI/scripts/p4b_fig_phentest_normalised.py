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
        ("base", "CTRL (TC5)", "k", "-", 2.2),
        ("tc10", "TC10", "tab:blue", "-.", 2.2),
        ("offon", "DL14+TC10", "tab:red", "--", 2.4),
        ("dayl", "DL13/12", "tab:green", "-", 2.0),
        ("dayl2", "DLtype", "tab:purple", "--", 2.0)]

regions, cur = [], None
import os
SUFFIX = "" if os.environ.get("REGSET", "default") == "default" else "_" + os.environ["REGSET"]   # same choice as p4
# POSTER=1: poster version with the diagnostic pilot only (GIMMS, CTRL, TC10, DL14+TC10) -> *_poster.png
POSTER = os.environ.get("POSTER", "0") == "1"
if POSTER:
    RUNS = [r for r in RUNS if r[0] in ("GIMMS", "base", "tc10", "offon")]
# POSTER_DL=1 (2026-10-12): DL14+TC10's autumn change is the 10 C threshold (day length < 14 h is always true by Sep
# at 50-70N), so the day-length-controlled run DL13/12 replaces it -> *_posterdl.png
POSTER_DL = os.environ.get("POSTER_DL", "0") == "1"
if POSTER_DL:
    RUNS = [r for r in RUNS if r[0] in ("GIMMS", "base", "tc10")] + [("dayl", "DL13/12", "tab:red", "--", 2.4)]
# BEST=1: GIMMS, CTRL and the best pilot (DL13/12, drawn in the main-run style) -> *_best.png
BEST = os.environ.get("BEST", "0") == "1"
if BEST:
    RUNS = [r for r in RUNS if r[0] in ("GIMMS", "base")] + [("dayl", "DL13/12", "tab:red", "--", 2.4)]
# REGIONS="NEU RFE NWN ESB": pick these AR6 codes (in this order) from both summary files -> 2x2 panel, *_<codes>.png
PICK = os.environ.get("REGIONS", "").split()
for fn in (["", "_dl"] if PICK else [SUFFIX]):
    for line in open("../data/phentest_regions_summary%s.txt" % fn):
        m = re.match(r"^(\S.*\(\w{3}\))\s+\(\d+ cells\)", line)
        if m:
            cur = {"name": m.group(1)}; regions.append(cur); continue
        m = re.match(r"^\s+(GIMMS|base|tc10|offon|dayl|dayl2)\s+((?:[\d.]+\s*){12})$", line.rstrip()) if cur else None
        if m:
            cur[m.group(1)] = np.array(m.group(2).split(), float)
if PICK:
    code = {r["name"][-4:-1]: r for r in regions}
    regions = [code[c] for c in PICK]
    SUFFIX = "_" + "_".join(PICK)

mon = np.arange(1, 13)
nr, nc_ = (2, 2) if len(regions) == 4 else (2, 3)
fig, axs = plt.subplots(nr, nc_, figsize=(10.5, 7.2) if nc_ == 2 else (15.5, 7.2), sharex=True, sharey=True)
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
fig.tight_layout()   # no suptitle (2026-10-08); definitions go in the caption
fig.savefig("../figures/fig3b_phentest_regions_normalised%s%s.png" % (SUFFIX, "_poster" if POSTER else "_posterdl" if POSTER_DL else "_best" if BEST else ""), dpi=200)
print("regions", len(regions), "| runs:", [k for k in regions[0] if k != "name"])
