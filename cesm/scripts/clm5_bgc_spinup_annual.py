#!/usr/bin/env python
# CLM5-BGC spin-up (AD 211 yr + post-AD 201 yr) -> one CSV of annual land means,
# for the 4-model spin-up figure.
#
# Weighting: area * landfrac over land gridcells, NON-ICE only: cells with
# PCT_GLACIER >= 50 % in the surface dataset are dropped (same idea as the
# non-ice masks of Noah-MP / LM4 / JULES).  Means are cos-free because area is
# the true cell area.
# AD phase: annual h0 (20 years per file), only GPP TLAI TOTVEGC TOTSOMC
#   TOTECOSYSC TWS exist -> soil T / soil water / snow are left empty.
#   Carbon pools there are in the accelerated (AD) state: expect a jump at the
#   AD -> post-AD boundary (notes 7l).
# post-AD: monthly h0, annual mean = mean of the 12 monthly fields per year.
# Units in the CSV: GPP gC/m2/d, carbon kgC/m2, TWS / H2OSNO mm, TSOI K,
# H2OSOI m3/m3 (mean of the 20 soil layers, thickness-unweighted).
import glob, os, re, sys
import numpy as np
from netCDF4 import Dataset

AD = "/data2/ydkoh/cesm2_output/clm5_bgc_ad/run"
PAD = "/home/ydkoh/CESM/spinup_raw/clm5_BGC_PAD"
SURF = ("/data1/CESM2_INPUT/lnd/clm2/surfdata_map/release-clm5.0.18/"
        "surfdata_0.9x1.25_hist_16pfts_Irrig_CMIP6_simyr2000_c190214.nc")
OUT = sys.argv[1] if len(sys.argv) > 1 else "/data2/ydkoh/cesm2_output/clm5_bgc_spinup_annual.csv"

f0 = sorted(glob.glob(f"{PAD}/clm5_bgc_pad.clm2.h0.0001-01.nc"))[0]
with Dataset(f0) as d:
    d.set_auto_mask(False)
    area = d.variables["area"][:].astype("f8"); lfr = d.variables["landfrac"][:].astype("f8")
    lmask = d.variables["landmask"][:]
with Dataset(SURF) as s:
    s.set_auto_mask(False)
    glac = s.variables["PCT_GLACIER"][:].astype("f8")
W = np.where((lmask > 0.5) & (glac < 50.0) & np.isfinite(area * lfr), area * lfr, 0.0)
print("weights: land cells %d, non-ice %d" % ((lmask > 0.5).sum(), (W > 0).sum()), flush=True)


def wm(a):
    a = np.asarray(a, "f8")
    m = np.isfinite(a) & (np.abs(a) < 1e30) & (W > 0)
    return float(np.sum(a[m] * W[m]) / np.sum(W[m]))


CARB = ["TOTVEGC", "TOTSOMC", "TOTECOSYSC"]
rows = []
# ---- AD: annual files, 20 records each -----------------------------------
for f in sorted(glob.glob(f"{AD}/clm5_bgc_ad.clm2.h0.????-01-01-00000.nc")):
    y0 = int(re.search(r"h0\.(\d{4})-", os.path.basename(f)).group(1))
    with Dataset(f) as d:
        d.set_auto_mask(False)
        for k in range(d.dimensions["time"].size):
            r = {"phase": "AD", "year": y0 + k,
                 "GPP": wm(d.variables["GPP"][k]) * 86400, "TLAI": wm(d.variables["TLAI"][k]),
                 "TWS": wm(d.variables["TWS"][k])}
            for v in CARB:
                r[v] = wm(d.variables[v][k]) / 1000.0
            rows.append(r)
    print("AD", os.path.basename(f), "done", flush=True)
nad = max(r["year"] for r in rows)
# ---- post-AD: monthly files ----------------------------------------------
years = sorted({int(re.search(r"h0\.(\d{4})-\d{2}", os.path.basename(f)).group(1))
                for f in glob.glob(f"{PAD}/clm5_bgc_pad.clm2.h0.????-??.nc")})
for y in years:
    files = sorted(glob.glob(f"{PAD}/clm5_bgc_pad.clm2.h0.{y:04d}-??.nc"))
    if len(files) < 12:
        continue
    acc = {}
    for f in files:
        with Dataset(f) as d:
            d.set_auto_mask(False)
            val = {"GPP": wm(d.variables["GPP"][0]) * 86400, "TLAI": wm(d.variables["TLAI"][0]),
                   "TWS": wm(d.variables["TWS"][0]), "H2OSNO": wm(d.variables["H2OSNO"][0]),
                   "TSOI_deep": wm(d.variables["TSOI"][0][19]),
                   "H2OSOI_col": wm(np.nanmean(np.where(np.abs(d.variables["H2OSOI"][0]) < 1e30,
                                                        d.variables["H2OSOI"][0], np.nan), 0))}
            for v in CARB:
                val[v] = wm(d.variables[v][0]) / 1000.0
        for k, v in val.items():
            acc.setdefault(k, []).append(v)
    r = {"phase": "postAD", "year": nad + y}
    r.update({k: float(np.mean(v)) for k, v in acc.items()})
    rows.append(r)
    if y % 20 == 0:
        print("postAD year", y, "done", flush=True)

cols = ["phase", "year", "GPP", "TLAI", "TOTVEGC", "TOTSOMC", "TOTECOSYSC", "TWS", "H2OSOI_col", "TSOI_deep", "H2OSNO"]
with open(OUT, "w") as fo:
    fo.write(",".join(cols) + "\n")
    for r in rows:
        fo.write(",".join(r["phase"] if c == "phase" else str(r["year"]) if c == "year"
                          else ("%.6g" % r[c] if c in r else "") for c in cols) + "\n")
print("wrote", OUT, len(rows), "rows (AD years 1..%d, post-AD %d..%d)" % (nad, nad + 1, nad + years[-1]))
