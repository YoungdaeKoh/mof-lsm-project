#!/usr/bin/env python3
"""Split the 2010 pilot-run NEE bias into GPP and ecosystem respiration (Reco = Ra + Rh).

Model (LM4+, land_month, all kg C m-2 yr-1 on soil_area -> g C m-2 d-1):
    Ra = gpp - npp ; Rh = rsoil ; Reco = Ra + Rh ; NEE = -nep   (closure NEE vs Reco - GPP is printed)
    resp (long_name "respiration") is reported to see which term it is.
Obs (FLUXCOM-X-BASE, same product family): GPP, NEE ; Reco_obs = NEE + GPP (no separate Reco downloaded;
    both are X-BASE model outputs, so Reco_obs inherits their errors).
Regions, weights and common cells as p21 (finite in all runs and in obs 2010 for 12 months).
Output: ../data/phentest_nee_decomp_2010.txt ; console = 50-70N summary.
usage: FLUXDIR=<dir with *_case.<var>.2010-2010.1deg.nc> python3 p22_phentest_nee_decomp.py
"""
import os
import warnings
import numpy as np
import netCDF4 as nc
import regionmask

warnings.simplefilter("ignore", RuntimeWarning)
FLUXDIR = os.environ["FLUXDIR"]
RUNS = [("base", "base_case", "CTRL"), ("tc10", "tc10_case", "TC10"), ("offon", "offon_d_case", "DL14+TC10"),
        ("dayl", "dayl_d_case", "DL13/12"), ("dayl2", "dayl2_d_case", "DLtype")]
YEAR = 2010
lat = -89.5 + np.arange(180)
lon = -179.5 + np.arange(360)
K = 1000.0 / 365.0


def model(case, var):
    with nc.Dataset("%s/%s.%s.%d-%d.1deg.nc" % (FLUXDIR, case, var, YEAR, YEAR)) as f:
        assert np.allclose(f["lat"][:], lat) and np.allclose(f["lon"][:], lon)
        a = np.ma.filled(f[var][:].astype(float), np.nan)
    a[np.abs(a) > 1e19] = np.nan
    return a * K


def fx(var, y):
    if var == "GPP":
        with nc.Dataset("../data/fluxcomx_gpp_monthly_1deg_2001_2021.nc") as f:
            t = nc.num2date(f["time"][:], f["time"].units)
            a = np.ma.filled(f["gpp"][:].astype(float), np.nan)
        return a[np.array([x.year for x in t]) == y]
    with nc.Dataset("/Volumes/data02/FLUXCOM_X_BASE/NEE_monthly_0.5deg/FLUXCOM-X-BASE_NEE_monthly_0.5deg_%d.nc" % y) as f:
        assert f["lat"][0] > 0 and f["lon"][0] < 0
        a = np.ma.filled(f["NEE"][:].astype(float), np.nan)[:, ::-1, :]
    return np.nanmean(a.reshape(12, 180, 2, 360, 2), axis=(2, 4))


obs = {"GPP": fx("GPP", YEAR), "NEE": fx("NEE", YEAR)}
obs["Reco"] = obs["NEE"] + obs["GPP"]
mod = {}
for k, c, _ in RUNS:
    g, n, rs, nep, resp = (model(c, v) for v in ("gpp", "npp", "rsoil", "nep", "resp"))
    mod[k] = {"GPP": g, "Ra": g - n, "Rh": rs, "Reco": g - n + rs, "NEE": -nep, "resp": resp}

ar6 = regionmask.defined_regions.ar6.land
rm = ar6.mask(lon, lat).values
masks = {c: rm == ar6.map_keys(c) for c in ("NEU", "RFE", "NWN", "ESB")}
masks["50-70N"] = np.isfinite(rm) & ((lat >= 50) & (lat <= 70))[:, None]
W = np.cos(np.radians(lat))[:, None] * np.ones((1, 360))
SEAS = {"DJF": [11, 0, 1], "MAM": [2, 3, 4], "MayJun": [4, 5], "Jul": [6], "Aug": [7], "SepOct": [8, 9], "ann": list(range(12))}

lines, summ = ["NEE decomposition, pilot runs 2010 vs FLUXCOM-X (g C m-2 d-1; NEE<0 uptake; Reco_obs = NEE+GPP)"], []
for reg, m in masks.items():
    ok = m & np.isfinite(obs["NEE"]).all(0) & np.isfinite(obs["GPP"]).all(0)
    for k in mod:
        for v in mod[k].values():
            ok &= np.isfinite(v).all(0)
    ww = W * ok
    avg = lambda a: np.array([np.nansum(a[i] * ww) / ww.sum() for i in range(12)])
    o = {v: avg(obs[v]) for v in obs}
    md = {k: {v: avg(mod[k][v]) for v in mod[k]} for k in mod}
    b = md["base"]
    lines.append("\n%s (%d cells)  closure max|NEE-(Reco-GPP)| CTRL = %.3f ; resp vs Ra / Reco (annual) = %.2f / %.2f / %.2f"
                 % (reg, ok.sum(), np.abs(b["NEE"] - (b["Reco"] - b["GPP"])).max(), b["resp"].mean(), b["Ra"].mean(), b["Reco"].mean()))
    lines.append("  %-14s" % "month" + "".join("%7d" % i for i in range(1, 13)))
    for v in ("GPP", "Reco", "NEE"):
        lines.append("  %-14s" % ("obs " + v) + "".join("%7.2f" % x for x in o[v]))
    for k, _, lab in RUNS:
        for v in ("GPP", "Ra", "Rh", "Reco", "NEE"):
            lines.append("  %-14s" % (lab + " " + v) + "".join("%7.2f" % x for x in md[k][v]))
    lines.append("  bias decomposition: dNEE = dReco - dGPP   (model - obs)")
    for k, _, lab in RUNS:
        for s, idx in SEAS.items():
            dg = md[k]["GPP"][idx].mean() - o["GPP"][idx].mean()
            dr = md[k]["Reco"][idx].mean() - o["Reco"][idx].mean()
            lines.append("    %-10s %-6s dNEE %+6.2f = dReco %+6.2f - dGPP %+6.2f  | Ra %5.2f Rh %5.2f (obs Reco %5.2f)"
                         % (lab, s, dr - dg, dr, dg, md[k]["Ra"][idx].mean(), md[k]["Rh"][idx].mean(), o["Reco"][idx].mean()))
    if reg == "50-70N":
        for k, _, lab in RUNS:
            if k not in ("base", "dayl"):
                continue
            for s in ("DJF", "MayJun", "Jul", "SepOct", "ann"):
                idx = SEAS[s]
                dg = md[k]["GPP"][idx].mean() - o["GPP"][idx].mean()
                dr = md[k]["Reco"][idx].mean() - o["Reco"][idx].mean()
                summ.append("%-8s %-6s obs GPP %5.2f Reco %5.2f NEE %+5.2f | model GPP %5.2f Ra %5.2f Rh %5.2f Reco %5.2f NEE %+5.2f | dNEE %+5.2f = dReco %+5.2f - dGPP %+5.2f"
                            % (lab, s, o["GPP"][idx].mean(), o["Reco"][idx].mean(), o["NEE"][idx].mean(),
                               md[k]["GPP"][idx].mean(), md[k]["Ra"][idx].mean(), md[k]["Rh"][idx].mean(),
                               md[k]["Reco"][idx].mean(), md[k]["NEE"][idx].mean(), dr - dg, dr, dg))
        summ.insert(0, [l for l in lines if l.startswith("\n50-70N")][0].strip())

open("../data/phentest_nee_decomp_2010.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(summ))
