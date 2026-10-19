#!/usr/bin/env python3
"""Does the spin-up / CO2 state change the phenology bias? FixCO2 (ctl, 292 ppm) vs HistCO2 (ctl2_co2) against GIMMS.

The two runs start from the same 1979 state (end of spin-up cycle 2) and differ only in CO2 (292 ppm fixed vs historical,
338 ppm in 1979 rising): by 1997 HistCO2 has +16 % GPP and +19 % wood carbon (p0b). If SOS/EOS biases are the same in both,
the phenology bias does not come from the carbon / CO2 state.
Both runs regridded with lm4p_to_latlon.py (same tool, 1982-1997, 1 deg). Method and regions = p24_sos_eos_three_obs.py
(regional cos-lat mean over cells valid in every product, monthly -> daily interpolation, per-year threshold, mean over years).
Obs: GIMMS LAI4g consolidated and AVHRR-only (GLASS starts 2001). Periods: 1982-1997 and its halves (drift of the difference).
Output: ../data/sos_eos_fixco2_vs_histco2.txt
"""
import warnings
import numpy as np
import netCDF4 as nc
import regionmask

MID = np.array([15.5, 45.0, 74.5, 105.0, 135.5, 166.0, 196.5, 227.5, 258.0, 288.5, 319.0, 349.5])
DOY = np.arange(1, 366)
PP = "/Volumes/data02/LM4P/postprocess/latlon/"
FILES = {"GIMMS-cons": ("../data/gimms_lai_mon_1982_2020.nc", 1982), "GIMMS-AVHRR": ("../data/gimms_solely_lai_mon_1982_2015.nc", 1982),
         "FixCO2": (PP + "lm4p_ctl_1979-2024.lai.1982-1997.1deg.nc", 1982), "HistCO2": (PP + "lm4p_ctl2_co2_1979-2023.lai.1982-1997.1deg.nc", 1982)}
OBS = ("GIMMS-cons", "GIMMS-AVHRR")


def read(fn, y0, a, b):
    with nc.Dataset(fn) as d:
        name = [v for v in d.variables if d.variables[v].ndim == 3][0]
        assert np.allclose(d["lat"][:], -89.5 + np.arange(180)) and np.allclose(d["lon"][:], -179.5 + np.arange(360))
        v = np.ma.filled(d.variables[name][(a - y0) * 12:(b - y0 + 1) * 12].astype("f8"), np.nan)
    assert v.shape[0] == (b - a + 1) * 12
    v[np.abs(v) > 100] = np.nan
    return v


def sos_eos(c, thr_f):
    lo, hi = c.min(), c.max(); thr = lo + thr_f * (hi - lo); ip = int(c.argmax())
    up = np.where((c[:-1] < thr) & (c[1:] >= thr))[0]; dn = np.where((c[:-1] >= thr) & (c[1:] < thr))[0]
    up = up[up < ip]; dn = dn[dn >= ip]; s = e = np.nan
    if up.size:
        i = up[-1]; s = DOY[i] + (thr - c[i]) / (c[i + 1] - c[i])
    if dn.size:
        i = dn[0]; e = DOY[i] + (c[i] - thr) / (c[i] - c[i + 1])
    return s, e


lat = -89.5 + np.arange(180); lon = -179.5 + np.arange(360)
W = np.cos(np.radians(lat))[:, None] * np.ones((1, 360))
ar6 = regionmask.defined_regions.ar6.land
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    m3 = ar6.mask_3D(lon, lat)
REG = {"50-70N land": m3.values.any(0) & ((lat >= 50) & (lat <= 70))[:, None]}
REG.update({c: m3.sel(region=ar6.map_keys(c)).values.astype(bool) for c in ("NEU", "RFE", "NWN", "ESB", "WSB", "NEN", "RAR")})

A, B = 1982, 1997
data = {p: read(f, y0, A, B) for p, (f, y0) in FILES.items()}
ok = np.all([np.isfinite(v).all(0) for v in data.values()], 0)
ny = B - A + 1
out = ["SOS/EOS %d-%d, 50 %% amplitude: FixCO2 (292 ppm) vs HistCO2 (historical CO2), same 1979 start state" % (A, B),
       "obs = mean of GIMMS-cons and GIMMS-AVHRR; dFix/dHist = model - obs; H-F = HistCO2 - FixCO2 (all years, 1982-89, 1990-97); sd = interannual sd of yearly H-F", ""]
out.append("%-12s %5s %-4s | %6s %6s | %6s %6s | %6s %6s %6s %5s" % ("region", "cells", "", "obs", "Fix", "dFix", "dHist", "H-F", "82-89", "90-97", "sd"))
for rn, rm in REG.items():
    w = W * (rm & ok)
    yearly = {}
    for p in FILES:
        ts = np.array([np.nansum(data[p][t] * w) / w.sum() for t in range(ny * 12)]).reshape(ny, 12)
        st = []
        for y in range(ny):
            pd = ts[y - 1, 11] if y > 0 else ts[y, 11]; nj = ts[y + 1, 0] if y < ny - 1 else ts[y, 0]
            c = np.interp(DOY, np.concatenate([[MID[-1] - 365], MID, [MID[0] + 365]]), np.concatenate([[pd], ts[y], [nj]]))
            st.append(sos_eos(c, 0.5))
        yearly[p] = np.array(st)
    for j, k in enumerate(("SOS", "EOS")):
        ob = np.nanmean([np.nanmean(yearly[p][:, j]) for p in OBS])
        fx, hs = yearly["FixCO2"][:, j], yearly["HistCO2"][:, j]
        hf = hs - fx
        out.append("%-12s %5d %-4s | %6.1f %6.1f | %+6.1f %+6.1f | %+6.1f %+6.1f %+6.1f %5.1f" % (
            rn if j == 0 else "", int((rm & ok).sum()), k, ob, np.nanmean(fx), np.nanmean(fx) - ob, np.nanmean(hs) - ob,
            np.nanmean(hf), np.nanmean(hf[:8]), np.nanmean(hf[8:]), np.nanstd(hf)))
open("../data/sos_eos_fixco2_vs_histco2.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
