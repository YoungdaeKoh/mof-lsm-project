#!/usr/bin/env python3
"""Is the GDD leaf-on gate already open before spring? GDD carried by leaf-OFF deciduous cohorts on 1 Jan 2011
(vegetation restart after the 2010 run), CTRL (base) vs DL13/12 (dayl_d) vs DL+tau5+hold (daylhold5_d).

LM4 resets a cohort's GDD to 0 at cold/photoperiod leaf-off and keeps accumulating (0 degC base) afterwards
(vegn_dynamics.F90:2158, vegetation.F90:2659), so warm days after leaf-off count toward next spring's gdd_crit.
gdd_crit: acer 360 (code default), c3grass 180 (field_table). Status 5 = LEAF_OFF. Unweighted cohort counts.
output: ../data/gdd_jan1_leafoff_2011.txt
"""
import numpy as np
from netCDF4 import Dataset

R = "/Volumes/data02/LM4P/cases/phentest_2010/"
RUNS = [("CTRL", "base"), ("DL", "dayl_d"), ("DLH5", "daylhold5_d")]
CRIT = {3: ("acer", 360.0), 5: ("c3grass", 180.0)}
BANDS = {"30-40N": (30, 40), "40-50N": (40, 50), "50-70N": (50, 70)}

L = ["GDD of leaf-OFF cohorts on 1 Jan 2011 (restart after 2010), unweighted; >=crit = gate already open"]
for name, run in RUNS:
    acc = {}
    for f in range(1, 7):
        with Dataset(R + "daylhold5_d/20100101.land_daily.tile%d.nc" % f) as A:      # same grid for all runs
            A.set_auto_mask(False)
            latof = dict(zip(A["grid_index"][:].astype(int).ravel(), A["geolat_t"][:].ravel()))
        with Dataset(R + run + "/RESTART_vegn/vegn2.res.tile%d.nc" % f) as A:
            A.set_auto_mask(False)
            NT = A.dimensions["tile"].size
            ci = A["cohort_index"][:].astype(np.int64)
            lat = np.array([latof[c] for c in (ci % (NT * 96 * 96)) % (96 * 96)])
            sp, st, g = A["species"][:], A["status"][:], A["gdd"][:]
            for s in CRIT:
                for b, (lo, hi) in BANDS.items():
                    m = (sp == s) & (st == 5) & (lat >= lo) & (lat < hi)
                    acc.setdefault((s, b), []).append(g[m])
    L.append("\n%s (%s)" % (name, run))
    for (s, b), v in sorted(acc.items()):
        g = np.concatenate(v); sn, cr = CRIT[s]
        L.append("  %-7s %s OFF %6d | GDD median %5.0f p90 %5.0f | >= crit %3.0f%% | zero %3.0f%%" % (
            sn, b, g.size, np.median(g), np.percentile(g, 90), 100 * np.mean(g >= cr), 100 * np.mean(g == 0)))
open("../data/gdd_jan1_leafoff_2011.txt", "w").write("\n".join(L) + "\n")
print("\n".join(L))
