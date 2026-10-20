#!/usr/bin/env python3
"""Is the Sep-Oct GPP drop of DL13/12 just the leaf-area drop? CTRL (base) vs DL13/12 (dayl_d), 2010, C96 cells.

Per cell, Sep-Oct mean LAI and GPP of both runs. If leaf efficiency is unchanged, the GPP ratio DL/CTRL equals the
ratio of absorbed light, approximated by Beer's law fAPAR = 1 - exp(-k LAI) (k = 0.5; also the best-fit k).
Also GPP per unit LAI and per unit fAPAR in both runs.
Cells: 40-70N, CTRL Sep-Oct LAI > 0.5. Plain means/medians (C96 quasi equal area).
output: ../data/gpp_vs_fapar_dl_2010.txt
"""
import glob
import numpy as np
from netCDF4 import Dataset

R = "/Volumes/data02/LM4P/cases/phentest_2010/"


def load(run):
    out = {"gpp": [], "lai": [], "lat": []}
    for f in sorted(glob.glob(R + run + "/20100101.land_month.tile*.nc")):
        with Dataset(f) as A:
            A.set_auto_mask(False)
            for v in ("gpp", "lai"):
                x = A[v][8:10].astype("f8"); x[np.abs(x) > 1e19] = np.nan; out[v].append(x.mean(0))
            out["lat"].append(A["geolat_t"][:].ravel())
    return {k: np.concatenate(v) for k, v in out.items()}


C, X = load("base"), load("dayl_d")
assert np.array_equal(C["lat"], X["lat"])
lat = C["lat"]
fap = lambda L, k=0.5: 1 - np.exp(-k * L)
out = ["Sep-Oct 2010, CTRL vs DL13/12, C96 cells with CTRL LAI > 0.5; gpp in kg C m-2 yr-1 (model units)",
       "%-7s %5s | %5s %5s %6s | %6s %6s | %8s %8s | %8s %8s | %5s" % ("band", "cells", "LAI_C", "LAI_X", "dLAI%", "dGPP%", "dfAP%",
                                                              "GPP/LAI_C", "GPP/LAI_X", "GPP/fAP_C", "GPP/fAP_X", "k_fit")]
for a, b in ((40, 50), (50, 60), (60, 70), (50, 70)):
    m = (lat >= a) & (lat < b) & np.isfinite(C["gpp"]) & np.isfinite(X["gpp"]) & (C["lai"] > 0.5) & np.isfinite(X["lai"])
    lc, lx, gc, gx = C["lai"][m].mean(), X["lai"][m].mean(), C["gpp"][m].mean(), X["gpp"][m].mean()
    fc, fx = fap(C["lai"][m]).mean(), fap(X["lai"][m]).mean()
    ks = np.arange(0.1, 1.51, 0.01)
    k = ks[np.argmin([abs(fap(X["lai"][m], k).mean() / fap(C["lai"][m], k).mean() - gx / gc) for k in ks])]
    out.append("%-7s %5d | %5.2f %5.2f %+6.1f | %+6.1f %+6.1f | %8.3f %8.3f | %8.3f %8.3f | %5.2f" % (
        "%d-%dN" % (a, b), m.sum(), lc, lx, 100 * (lx / lc - 1), 100 * (gx / gc - 1), 100 * (fx / fc - 1),
        gc / lc, gx / lx, gc / fc, gx / fx, k))
# cell-level: how well does the fAPAR ratio predict the GPP ratio?
m = (lat >= 50) & (lat < 70) & (C["lai"] > 0.5) & (C["gpp"] > 0.05) & np.isfinite(X["gpp"]) & np.isfinite(X["lai"])
rg = X["gpp"][m] / C["gpp"][m]; rf = fap(X["lai"][m]) / fap(C["lai"][m])
out += ["", "50-70N cell level (n %d): GPP ratio median %.3f, fAPAR ratio median %.3f, r(GPP ratio, fAPAR ratio) %.2f, "
        "median |GPP ratio - fAPAR ratio| %.3f" % (m.sum(), np.median(rg), np.median(rf), np.corrcoef(rg, rf)[0, 1], np.median(np.abs(rg - rf)))]
open("../data/gpp_vs_fapar_dl_2010.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
