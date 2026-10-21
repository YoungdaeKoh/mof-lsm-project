#!/usr/bin/env python3
"""Offline emulation: how much later would acer leaf on in spring if GDD restarted on 1 January, instead of carrying the
GDD accumulated since the last autumn leaf-off (LM4 design, vegn_dynamics.F90:2158 / vegetation.F90:2659)?

Weather: the run's own 2010 daily leaf temperature (land_daily vegn_temp_max/min, C96 cell mean) as a proxy for the
canopy-air Tmin/Tmax the model uses (cana_T is not in the daily output); tc_daily ~ (Tmax+Tmin)/2.
Acer leaf-on gate per cell, day by day (order as update_vegn_slow: GDD, smoothers, then test):
  GDD += [max(Tmin-0C,0) + max(Tmax-0C,0)]/2 ;  tc20 = 0.95 tc20 + 0.05 tc ;  tc5 = 0.8 tc5 + 0.2 tc (tc5 starts at tc20)
  rules 'DL'  : GDD > 360 and tc20 >= 10 C
  rules 'DLH5': GDD > 360 and tc5 >= 10 C and not(day length < 12 h and tc20 < 20 C)
  (drought ignored). tc20 starts from the tile-mean tc_pheno of the seed restart.
Initial GDD per cell = median over leaf-OFF acer cohorts on 1 Jan:
  S0  seed ctl y2009 (what the 2010 runs actually started from) -> validation against the run's own leaf-on
  A   2011 restart of the same rule set (carry-over, = year 2 of a multi-year run)
  B   0 (proposed reset on 1 Jan)
Validation: model leaf-on from daily LAI (first day > LAI(doy1) + 10 % of the 2010 range) in cells where acer holds
>= 50 % of July leaf area (land_month_by_species), compared with the S0 gate.
Unweighted cell medians. output: ../data/gdd_jan1_reset_offline_2010.txt
"""
import numpy as np
import shapely
import regionmask
from netCDF4 import Dataset

P = "/Volumes/data02/LM4P/cases/phentest_2010/"
RUNS = {"DL": "dayl_d", "DLH5": "daylhold5_d"}
GROUPS = ["ENA", "EAS", "WCE", "40-50N", "30-40N", "NEU", "50-70N"]
NEED = {"ENA": 23, "EAS": 59, "WCE": -4, "40-50N": 15, "NEU": -6, "50-70N": -8}   # -(DLS5 SOS bias), p26


def cell_gdd(path):
    """median GDD of leaf-OFF acer cohorts and mean tc_pheno per (face, flat cell)"""
    g, t = {}, {}
    for f in range(1, 7):
        with Dataset(path % f) as A:
            A.set_auto_mask(False)
            NT = A.dimensions["tile"].size
            ci = A["cohort_index"][:].astype(np.int64); ti = A["tile_index"][:].astype(np.int64)
            cc = (ci % (NT * 96 * 96)) % (96 * 96)
            m = (A["species"][:] == 3) & (A["status"][:] == 5)
            for c, v in zip(cc[m], A["gdd"][:][m]):
                g.setdefault((f, c), []).append(v)
            for c, v in zip(ti % (96 * 96), A["tc_pheno"][:]):
                t.setdefault((f, c), []).append(v)
    return {k: np.median(v) for k, v in g.items()}, {k: np.mean(v) for k, v in t.items()}


seed_g, seed_t = cell_gdd(P + "seed_ctl_y2009/vegn2.res.tile%d.nc")
carry = {r: cell_gdd(P + run + "/RESTART_vegn/vegn2.res.tile%d.nc")[0] for r, run in RUNS.items()}

out = {r: {} for r in RUNS}
for r, run in RUNS.items():
    keys, lat, lon, gates, valid = [], [], [], {s: [] for s in ("S0", "A", "B")}, []
    for f in range(1, 7):
        with Dataset(P + run + "/20100101.land_daily.tile%d.nc" % f) as A:
            A.set_auto_mask(False)
            gi = A["grid_index"][:].astype(int).ravel()
            tx = A["vegn_temp_max"][:].astype("f8") - 273.15; tn = A["vegn_temp_min"][:].astype("f8") - 273.15
            lai = A["lai"][:].astype("f8")
            la = A["geolat_t"][:].ravel(); lo = A["geolon_t"][:].ravel()
        with Dataset(P + run + "/20100101.land_month_by_species.tile%d.nc" % f) as A:
            A.set_auto_mask(False)
            sl = A["lai"][6, :6].astype("f8"); sl[(sl < 0) | (sl > 1e10)] = 0
        acer_share = sl[3] / np.maximum(sl.sum(0), 1e-9)
        bad = (np.abs(tx) > 200) | (np.abs(tn) > 200)
        tx[bad] = np.nan; tn[bad] = np.nan
        lai[(lai < 0) | (lai > 1e10)] = np.nan
        doy = np.arange(1, 366)
        decl = 23.44 * np.pi / 180 * np.sin(2 * np.pi * (284 + doy) / 365)
        for n, c in enumerate(gi):
            k = (f, c)
            if k not in seed_g or k not in carry[r] or k not in seed_t or np.isnan(tx[:, n]).any():
                continue
            phi = np.deg2rad(la[n])
            dayl = 24 / np.pi * np.arccos(np.clip(-np.tan(phi) * np.tan(decl), -1, 1))
            tcd = 0.5 * (tx[:, n] + tn[:, n])
            dg = 0.5 * (np.maximum(tn[:, n], 0) + np.maximum(tx[:, n], 0))
            t20 = np.empty(365); t5 = np.empty(365); a20 = seed_t[k] - 273.15; a5 = a20
            for d in range(365):
                a20 = 0.95 * a20 + 0.05 * tcd[d]; a5 = 0.8 * a5 + 0.2 * tcd[d]
                t20[d] = a20; t5[d] = a5
            for s, g0 in (("S0", seed_g[k]), ("A", carry[r][k]), ("B", 0.0)):
                G = g0 + np.cumsum(dg)
                if r == "DL":
                    ok = (G > 360) & (t20 >= 10)
                else:
                    ok = (G > 360) & (t5 >= 10) & ~((dayl < 12) & (t20 < 20))
                ok[200:] = False                                    # spring only (doy <= 200)
                gates[s].append(np.argmax(ok) + 1 if ok.any() else np.nan)
            l = lai[:, n]; rng = np.nanmax(l) - np.nanmin(l)
            on = np.where(l > l[0] + 0.1 * rng)[0]
            valid.append(on[0] + 1 if (acer_share[n] >= 0.5 and rng > 0.3 and on.size) else np.nan)
            keys.append(k); lat.append(la[n]); lon.append(lo[n])
    out[r] = dict(lat=np.array(lat), lon=np.array(lon), valid=np.array(valid),
                  **{s: np.array(v, dtype="f8") for s, v in gates.items()})

ar6 = regionmask.defined_regions.ar6.land
L = ["Offline acer leaf-on gate (doy), 2010 daily leaf T, initial GDD: S0 seed / A carried (2011 restart) / B reset 1 Jan",
     "delay = median(B - A) over cells; need = days the DLS5 run must move later (p26); model = run's own leaf-on, acer>=50 % cells"]
for r in RUNS:
    o = out[r]
    pts = shapely.points(np.where(o["lon"] > 180, o["lon"] - 360, o["lon"]), o["lat"])
    L.append("\nrules %s" % r)
    L.append("  %-7s %5s | %5s %5s %5s | %6s %8s %6s %7s | %5s | valid n  S0  model" % (
        "group", "cells", "S0", "A", "B", "B-A", "%B>A", "mean", "if>0", "need"))
    for g in GROUPS:
        if g[0].isdigit():
            lo_, hi_ = [float(x) for x in g[:-1].split("-")]
            m = (o["lat"] >= lo_) & (o["lat"] < hi_)
        else:
            m = shapely.contains(ar6[[g]].polygons[0], pts)
        m &= np.isfinite(o["A"]) & np.isfinite(o["B"]) & np.isfinite(o["S0"])
        if m.sum() < 5:
            continue
        d = o["B"][m] - o["A"][m]
        v = m & np.isfinite(o["valid"])
        L.append("  %-7s %5d | %5.0f %5.0f %5.0f | %+6.0f %7.0f%% %+6.1f %+7.0f | %5s | %5d %5.0f %5.0f" % (
            g, m.sum(), np.median(o["S0"][m]), np.median(o["A"][m]), np.median(o["B"][m]), np.median(d), 100 * np.mean(d > 0),
            d.mean(), np.median(d[d > 0]) if (d > 0).any() else 0.0,
            "%+d" % NEED[g] if g in NEED else "-", v.sum(),
            np.median(o["S0"][v]) if v.any() else np.nan, np.median(o["valid"][v]) if v.any() else np.nan))
open("../data/gdd_jan1_reset_offline_2010.txt", "w").write("\n".join(L) + "\n")
print("\n".join(L))
