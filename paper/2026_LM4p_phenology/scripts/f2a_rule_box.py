#!/usr/bin/env python3
"""Fig. 2a: phenology rule box of the poster (poster/2026_LM4p_LAI/scripts/p15_phenology_rule_box.py, Weng et al. 2015
Eq. A31) with the terms added in this study in red: winter hold (leaf-on) and photoperiod leaf-off (autumn).
The spring change (5-day smoothing for leaf-on) is deliberately not shown here (user choice 2026-10-19).
Patch: lm4/patches/lm4P.phenology_autumn_daylength.diff, lm4P.phenology_winter_hold.diff
  leaf-off also if days shortening and dayl < dayl_crit_off and T_pheno < tc_crit_off (20 C)
  leaf-on blocked while dayl < dayl_crit_on (12 h) and T_pheno < tc_crit_off
output: ../figures/f2a_rule_box.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

G = "#14532d"; RED = "#c0392b"
rows = [   # (text, side note, kind, colour)
    ("Phenology rule (Weng et al., 2015, Eq. A31) and the terms added in this study (red)", None, "head", G),
    (r"$GDD(t) = \sum_{i=1}^{t} \max\left[T_d(i) - 0^\circ\mathrm{C},\ 0\right]$", "t = days since the end of the last growing season", "eq", "k"),
    (r"$T_{pheno}(t) = 0.95\,T_{pheno}(t-1) + 0.05\,T_d(t)$", "weighted mean daily temperature (memory ≈ 20 d)", "eq", "k"),
    ("Leaf-on", None, "head", G),
    (r"$GDD(t) > GDD_{crit}\quad \mathrm{and}\quad T_{pheno}(t) > T_{crit}$", "", "eq", "k"),
    (r"$\mathrm{and\ not}\ \left[\,L_{day}(t) < 12\,\mathrm{h}\quad \mathrm{and}\quad T_{pheno}(t) < 20^\circ\mathrm{C}\,\right]$", "winter hold: no re-greening after the solstice", "eq", RED),
    ("Leaf-off", None, "head", G),
    (r"$T_{pheno}(t) < T_{crit}$", "LM4.1: temperature is the only autumn cue", "eq", "k"),
    (r"$\mathrm{or}\ \left[\,\mathrm{days\ shortening}\quad \mathrm{and}\quad L_{day}(t) < L_{crit}\quad \mathrm{and}\quad T_{pheno}(t) < 20^\circ\mathrm{C}\,\right]$", "photoperiod leaf-off", "eq", RED),
    (r"$T_{crit}$ = 5$^\circ$C (larch, C3 grass), 10$^\circ$C (other deciduous);  $L_{day}$ = day length from latitude and date", None, "note", "0.25"),
    (r"$L_{crit}$ = 13 h (larch, C3 grass), 12 h (broadleaf deciduous); evergreen and tropical species unchanged", None, "note", RED),
]
STEP = {"head": 0.42, "note": 0.42, "eq": 0.50}
H = 0.25 + sum(STEP[k] + (0.25 if "sum" in t else 0) for t, _, k, _ in rows) + 0.15
W = 14.5
fig = plt.figure(figsize=(W, H))
ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, W); ax.set_ylim(0, H)
ax.add_patch(plt.Rectangle((0.04, 0.04), W - 0.08, H - 0.08, fill=False, ec=G, lw=2))
y = H - 0.25
for txt, note, kind, col in rows:
    tall = 0.25 if "sum" in txt else 0
    y -= (STEP[kind] + tall) / 2
    if kind == "head":
        ax.text(0.3, y, txt, fontsize=15, weight="bold", color=col, va="center")
    elif kind == "note":
        ax.text(0.6, y, txt, fontsize=12.5, color=col, va="center")
    else:
        ax.text(0.6, y, txt, fontsize=16, va="center", color=col)
        if note:
            ax.text(9.6, y, note, fontsize=11.5, color=RED if col == RED else "0.35", va="center", style="italic")
    y -= (STEP[kind] + tall) / 2
fig.savefig("../figures/f2a_rule_box.png", dpi=220)
print("wrote ../figures/f2a_rule_box.png, height %.2f in, bottom margin %.2f in" % (H, y))
