#!/usr/bin/env python3
"""Poster box: the leaf-on / leaf-off rule written as in Weng et al. (2015, Eq. A31) (user choice 2026-10-08: cite the paper, do not show code).

Source lines (server /data2/ydkoh/lm4/esm4p5-lm4p-offline/src/lm4P/vegetation/):
  vegetation.F90:2659-2664   daily GDD (mean of Tmin, Tmax excess over gdd_base_T = 0 C) and tc_pheno EMA (0.95 / 0.05)
  vegn_dynamics.F90 vegn_phenology_ppa   LEAF_OFF -> LEAF_ON if gdd > gdd_crit and tc_pheno >= tc_crit and not drought;
                                         LEAF_ON -> LEAF_OFF if tc_pheno < tc_crit (gdd reset) or drought; leaf_fall_rate 0.075 d-1
  field_table (ctl): larix, c3grass tc_crit = 278.15 K, gdd_crit = 180; others code default 283.16 K, 360
  patch lm4P.phenology_autumn_daylength.diff: extra leaf-off if shortening and dayl < dayl_crit_off and tc_pheno < tc_crit_off
output: ../figures/box_phenology_rule.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

G = "#14532d"
rows = [   # written as in Weng et al. (2015, Biogeosciences 12, 2655, Appendix A3, Eq. A31), not as code
    ("Phenology rule (Weng et al., 2015, Eq. A31)", None, "head"),
    (r"$GDD(t) = \sum_{i=1}^{t} \max\left[T_d(i) - 0^\circ\mathrm{C},\ 0\right]$", "t = days since the end of the last growing season", "eq"),
    (r"$T_{pheno}(t) = 0.95\,T_{pheno}(t-1) + 0.05\,T_d(t)$", "weighted mean daily temperature (memory ≈ 20 d)", "eq"),
    ("Leaf-on", None, "head"),
    (r"$GDD(t) > GDD_{crit}\quad \mathrm{and}\quad T_{pheno}(t) > T_{crit}$", "", "eq"),
    ("Leaf-off", None, "head"),
    (r"$T_{pheno}(t) < T_{crit}$", "temperature is the only autumn cue", "eq"),
    (r"$T_{crit}$ = 5$^\circ$C (larch, C3 grass), 10$^\circ$C (other deciduous) in the LM4+ configuration used here", None, "note"),
]
# line heights in inches (absolute, so the box height follows the content); the GDD line has a tall summation sign
STEP = {"head": 0.42, "head2": 0.42, "note": 0.48, "eq": 0.50}
H = 0.25 + sum(STEP[k] + (0.25 if "sum" in t else 0) for t, _, k in rows) + 0.15
W = 14.5
fig = plt.figure(figsize=(W, H))
ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, W); ax.set_ylim(0, H)
ax.add_patch(plt.Rectangle((0.04, 0.04), W - 0.08, H - 0.08, fill=False, ec=G, lw=2))
y = H - 0.25
for txt, note, kind in rows:
    tall = 0.25 if "sum" in txt else 0
    y -= (STEP[kind] + tall) / 2
    if kind in ("head", "head2"):
        ax.text(0.3, y, txt, fontsize=15, weight="bold", color=G if kind == "head" else "#b91c1c", va="center")
    elif kind == "note":
        ax.text(0.6, y, txt, fontsize=13, color="0.25", va="center")
    else:
        ax.text(0.6, y, txt, fontsize=16, va="center")
        if note:
            ax.text(9.0, y, note, fontsize=12, color="0.35", va="center", style="italic")
    y -= (STEP[kind] + tall) / 2
fig.savefig("../figures/box_phenology_rule.png", dpi=220)
print("wrote ../figures/box_phenology_rule.png, height %.2f in, bottom margin %.2f in" % (H, y))
