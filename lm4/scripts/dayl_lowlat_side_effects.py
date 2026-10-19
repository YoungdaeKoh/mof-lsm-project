#!/usr/bin/env python3
"""Side effects of the autumn day-length rule (DL13/12) outside the boreal zone, 2010: dayl_d vs base (CTRL), C96 grid.

(1) Tropics (20S-20N) and southern extratropics (20-60S): where can the rule fire, and how much LAI is lost?
    Rule for larix/c3grass (vegn_dynamics.F90 patch): shortening .and. dayl < 13 h .and. tc_pheno < 20 C
    (acer 12 h). In the tropics dayl < 13 h holds for the whole shortening half-year, so only tc_pheno < 20 C decides.
    "rule days" = days meeting the c3grass condition, tc_pheno reconstructed as the 20-day EMA of daily canopy Tmean
    (dayl_d daily vegn_temp_max/min, as spring_gate_diag.py). Cells split into rule days > 0 ("cool") and = 0.
(2) Subtropics 20-40N: is the SOS shift (-28 d at 50 % amplitude, p8) real or a threshold artefact?
    SOS from monthly LAI interpolated to days (as p8), once with each run's own amplitude, once with CTRL's
    threshold (CTRL min + 50 % of CTRL range) applied to both runs. A metric artefact shows up as a large own-amplitude
    shift that disappears with the fixed threshold, together with a lower winter (Jan-Feb) minimum.
Unweighted cell statistics on C96 (cubed sphere ~equal area). Cells with annual-max LAI > 0.1.
usage: python3 dayl_lowlat_side_effects.py -> ../data/dayl_lowlat_side_effects_2010.txt
"""
import glob
import numpy as np
from netCDF4 import Dataset

R = "/Volumes/data02/LM4P/cases/phentest_2010/"
MID = np.array([15.5, 45, 74.5, 105, 135.5, 166, 196.5, 227.5, 258, 288.5, 319, 349.5]); D = np.arange(1, 366.0)


def load(run, kind, var):
    out, la, lo = [], [], []
    for f in sorted(glob.glob(R + run + "/*.land_%s.tile*.nc" % kind)):
        with Dataset(f) as A:
            A.set_auto_mask(False)
            x = A[var][:].astype("f8"); out.append(x.reshape(x.shape[0], -1))
            la.append(A["geolat_t"][:].ravel()); lo.append(A["geolon_t"][:].ravel())
    return np.concatenate(out, -1), np.concatenate(la), np.concatenate(lo)


lb, lat, lon = load("base", "month", "lai")
ld, lat2, _ = load("dayl_d", "month", "lai")
assert np.array_equal(lat, lat2) and lb.shape[0] == 12
tx, _, _ = load("dayl_d", "daily", "vegn_temp_max"); tn, _, _ = load("dayl_d", "daily", "vegn_temp_min")
ok = np.all((lb >= 0) & (lb < 1e10) & (ld >= 0) & (ld < 1e10), 0) & np.all((tx > 100) & (tx < 400), 0) & (lb.max(0) > 0.1)

tm = (tx + tn) / 2 - 273.15; tc = np.empty_like(tm); tc[0] = tm[:31].mean(0)
for t in range(1, tm.shape[0]):
    tc[t] = 0.95 * tc[t - 1] + 0.05 * tm[t]
d = np.arange(1, tm.shape[0] + 1)[:, None]; rl = np.radians(lat)[None, :]
decl = np.radians(23.44) * np.sin(2 * np.pi * (284 + d) / 365)
dayl = 24 / np.pi * np.arccos(np.clip(-np.tan(rl) * np.tan(decl), -1, 1))
shorten = (rl * np.cos(2 * np.pi * (284 + d) / 365)) < 0
rule_days = (shorten & (dayl < 13) & (tc < 20)).sum(0)

ann_b, ann_d = lb.mean(0), ld.mean(0)
out = ["DL13/12 (dayl_d) vs CTRL (base), 2010, C96 cells with max LAI > 0.1; LAI from land_month", "",
       "(1) where the rule can fire (c3grass condition, rule days from reconstructed tc_pheno) and annual-mean LAI change",
       "%-22s %6s | %8s %8s %7s | %7s %7s | %s" % ("group", "cells", "LAI CTRL", "LAI DL", "dLAI%", "min dL%", "<-5%", "rule days median")]
for name, m in (("20S-20N rule days = 0", ok & (np.abs(lat) < 20) & (rule_days == 0)),
                ("20S-20N rule days > 0", ok & (np.abs(lat) < 20) & (rule_days > 0)),
                ("20-60S rule days = 0", ok & (lat <= -20) & (lat > -60) & (rule_days == 0)),
                ("20-60S rule days > 0", ok & (lat <= -20) & (lat > -60) & (rule_days > 0)),
                ("20-40N (all)", ok & (lat >= 20) & (lat < 40)),
                ("50-70N (all, reference)", ok & (lat >= 50) & (lat < 70))):
    if m.sum() == 0:
        out.append("%-22s %6d" % (name, 0)); continue
    dl = 100 * (ann_d[m] / ann_b[m] - 1)
    mn = 100 * (ld.min(0)[m] / np.maximum(lb.min(0)[m], 1e-3) - 1)
    out.append("%-22s %6d | %8.2f %8.2f %+7.1f | %+7.1f %6.0f%% | %5.0f" % (name, m.sum(), ann_b[m].mean(), ann_d[m].mean(),
               100 * (ann_d[m].sum() / ann_b[m].sum() - 1), np.median(mn), 100 * np.mean(dl < -5), np.median(rule_days[m])))
    if "> 0" in name:
        out.append("%-22s        lat median %.1f, annual Tmean median %.1f C, cells losing >20 %% annual LAI: %d"
                   % ("", np.median(lat[m]), np.median(tm[:, m].mean(0)), int(np.sum(dl < -20))))


def sos(m12, thr):
    c = np.interp(D, np.r_[MID[-1] - 365, MID, MID[0] + 365], np.r_[m12[-1], m12, m12[0]])
    ip = int(c.argmax()); up = [k for k in range(ip) if c[k] < thr <= c[k + 1]]
    return D[up[-1]] + (thr - c[up[-1]]) / (c[up[-1] + 1] - c[up[-1]]) if up else np.nan


m = ok & (lat >= 20) & (lat < 40) & (lb.max(0) - lb.min(0) >= 0.3)
idx = np.where(m)[0]
own_b = np.array([sos(lb[:, i], lb[:, i].min() + 0.5 * np.ptp(lb[:, i])) for i in idx])
own_d = np.array([sos(ld[:, i], ld[:, i].min() + 0.5 * np.ptp(ld[:, i])) for i in idx])
fix_d = np.array([sos(ld[:, i], lb[:, i].min() + 0.5 * np.ptp(lb[:, i])) for i in idx])
jf_b, jf_d = lb[:2, idx].mean(0), ld[:2, idx].mean(0)
amj_b, amj_d = lb[3:6, idx].mean(0), ld[3:6, idx].mean(0)
v = np.isfinite(own_b) & np.isfinite(own_d) & np.isfinite(fix_d)
out += ["", "(2) subtropics 20-40N, cells with CTRL amplitude >= 0.3: %d (%d with SOS in all three)" % (idx.size, v.sum()),
        "  SOS shift DL - CTRL, own 50 %% amplitude : median %+.1f d, mean %+.1f d" % (np.median((own_d - own_b)[v]), np.mean((own_d - own_b)[v])),
        "  SOS shift DL - CTRL, CTRL's threshold    : median %+.1f d, mean %+.1f d" % (np.median((fix_d - own_b)[v]), np.mean((fix_d - own_b)[v])),
        "  Jan-Feb LAI   CTRL %.2f -> DL %.2f (%+.1f %%)" % (jf_b.mean(), jf_d.mean(), 100 * (jf_d.sum() / jf_b.sum() - 1)),
        "  Apr-Jun LAI   CTRL %.2f -> DL %.2f (%+.1f %%)" % (amj_b.mean(), amj_d.mean(), 100 * (amj_d.sum() / amj_b.sum() - 1)),
        "  annual max    CTRL %.2f -> DL %.2f" % (lb.max(0)[idx].mean(), ld.max(0)[idx].mean())]
open("../data/dayl_lowlat_side_effects_2010.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
