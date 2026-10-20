#!/usr/bin/env python3
"""Interannual temperature sensitivity of EOS and SOS (days per K): observations vs LM4p CTRL, 1982-2015.

Per 1-deg cell and year: SOS / EOS = 50 % amplitude crossings of that year's monthly LAI (interpolated to days,
the year's own min/max), as Fig. 1 but year by year. Temperature: ERA5 monthly t2m (0.25 deg, NH; grid checked
2026-10-20: lat 90->0, lon 0-359.75, K, raw index plot = NH map) averaged to 1 deg (4 x 4 nodes). Windows follow
Park & Jeong 2021 (ERL): T_EOS = mean of the 3 months centred on the cell's climatological EOS month; T_SOS =
the climatological SOS month and the 2 months before (preseason). Slope = OLS of detrended EOS (SOS) on detrended T
per cell (>= 25 valid years). Note: the model was forced by WFDE5 (ERA5-based, bias-adjusted), not ERA5 itself.
Obs: GIMMS LAI4g consolidated and GIMMS AVHRR-only; model: lm4p_ctl 1982-2020 monthly LAI (1 deg).
Cells: 25-75N, GIMMS climatological amplitude >= 0.5, model climatological amplitude >= 0.3, finite everywhere.
output: ../data/s8_eos_temp_sensitivity.txt
"""
import warnings
import shapely
import numpy as np
import netCDF4 as nc
import regionmask
from scipy import stats

Y0, Y1 = 1982, 2015; NY = Y1 - Y0 + 1
D = np.arange(1, 366.0)
MID = np.array([15.5, 45, 74.5, 105, 135.5, 166, 196.5, 227.5, 258, 288.5, 319, 349.5])
P = "../../../poster/2026_LM4p_LAI/data/"
FILES = {"GIMMS": (P + "gimms_lai_mon_1982_2020.nc", 1982), "AVHRR": (P + "gimms_solely_lai_mon_1982_2015.nc", 1982),
         "CTRL": ("/Volumes/data02/LM4P/postprocess/latlon/lm4p_ctl_1979-2024.lai.1982-2020.1deg.nc", 1982)}
lat = -89.5 + np.arange(180); lon = -179.5 + np.arange(360)


def read(fn, y0):
    with nc.Dataset(fn) as d:
        assert np.allclose(d["lat"][:], lat) and np.allclose(d["lon"][:], lon)
        name = [v for v in d.variables if d.variables[v].ndim == 3][0]
        v = np.ma.filled(d.variables[name][(Y0 - y0) * 12:(Y1 - y0 + 1) * 12].astype("f8"), np.nan)
    v[np.abs(v) > 100] = np.nan
    return v.reshape(NY, 12, 180, 360)


L = {k: read(*FILES[k]) for k in FILES}
with nc.Dataset("/Volumes/data02/ERA5/ERA5m_t2m_NH_1979-2023.nc") as A:
    assert np.isclose(A["latitude"][0], 90) and np.isclose(A["longitude"][0], 0) and A["t2m"].units == "K"
    x = A["t2m"][(Y0 - 1979) * 12:(Y1 - 1979 + 1) * 12].astype("f4")
x = x[:, ::-1][:, :360]                                                     # lat 0.0 .. 89.75 ascending
x = np.roll(x, -720, axis=2)                                                # lon -180 .. 179.75
T1 = x.reshape(NY * 12, 90, 4, 360, 4).mean((2, 4)) - 273.15               # 1-deg cells, lat 0.5 .. 89.5
T = np.full((NY, 12, 180, 360), np.nan); T[:, :, 90:] = T1.reshape(NY, 12, 90, 360)


def dates(m):
    c = np.interp(D, np.r_[MID[-1] - 365, MID, MID[0] + 365], np.r_[m[-1], m, m[0]])
    thr = c.min() + 0.5 * (c.max() - c.min()); ip = int(c.argmax())
    up = [k for k in range(ip) if c[k] < thr <= c[k + 1]]; dn = [k for k in range(ip, 364) if c[k] >= thr > c[k + 1]]
    s = D[up[-1]] + (thr - c[up[-1]]) / (c[up[-1] + 1] - c[up[-1]]) if up else np.nan
    e = D[dn[0]] + (c[dn[0]] - thr) / (c[dn[0]] - c[dn[0] + 1]) if dn else np.nan
    return s, e


LA = lat[:, None] * np.ones((1, 360))
clim = {k: np.nanmean(v, 0) for k, v in L.items()}
ok = (LA >= 25) & (LA < 75) & np.isfinite(T).all((0, 1))
for k, v in L.items():
    ok &= np.isfinite(v).all((0, 1))
ok &= (clim["GIMMS"].max(0) - clim["GIMMS"].min(0) >= 0.5) & (clim["CTRL"].max(0) - clim["CTRL"].min(0) >= 0.3)
yrs = np.arange(NY)
res = {k: {"EOS": np.full((180, 360), np.nan), "SOS": np.full((180, 360), np.nan),
           "pE": np.full((180, 360), np.nan), "pS": np.full((180, 360), np.nan)} for k in L}


def slope(e, t):
    v = np.isfinite(e) & np.isfinite(t)
    if v.sum() < 25:
        return np.nan, np.nan
    e = e[v] - np.polyval(np.polyfit(yrs[v], e[v], 1), yrs[v]); t = t[v] - np.polyval(np.polyfit(yrs[v], t[v], 1), yrs[v])
    r = stats.linregress(t, e); return r.slope, r.pvalue


for i, j in zip(*np.where(ok)):
    for k, v in L.items():
        sc, ec = dates(clim[k][:, i, j])
        if not (np.isfinite(sc) and np.isfinite(ec)):
            continue
        me = min(int(ec // 30.42), 11); ms = min(int(sc // 30.42), 11)
        tE = T[:, [(me - 1) % 12, me, (me + 1) % 12], i, j].mean(1)
        tS = T[:, [(ms - 2) % 12, (ms - 1) % 12, ms], i, j].mean(1)
        se = np.array([dates(v[y, :, i, j]) for y in range(NY)])
        res[k]["EOS"][i, j], res[k]["pE"][i, j] = slope(se[:, 1], tE)
        res[k]["SOS"][i, j], res[k]["pS"][i, j] = slope(se[:, 0], tS)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    reg = regionmask.defined_regions.ar6.land.mask(lon, lat).values
GROUPS = [("25-75N", LA >= 25), ("40-50N", (LA >= 40) & (LA < 50)), ("50-70N", (LA >= 50) & (LA < 70))] + \
         [(c, reg == regionmask.defined_regions.ar6.land.map_keys(c)) for c in ("NWN", "NEN", "ENA", "NEU", "WCE", "EEU", "WSB", "ESB", "RFE", "EAS", "TIB")]
out = ["Interannual sensitivity, %d-%d, detrended OLS per cell, median over cells (d/K); sig = %% cells p < 0.05" % (Y0, Y1),
       "EOS: T = 3 months centred on climatological EOS month; SOS: T = SOS month and 2 months before (Park & Jeong 2021 windows)",
       "%-7s %5s | %-26s | %-26s" % ("region", "cells", "EOS  GIMMS  AVHRR  CTRL", "SOS  GIMMS  AVHRR  CTRL")]
for name, g in GROUPS:
    m = ok & g
    for k in L:
        m = m & np.isfinite(res[k]["EOS"]) & np.isfinite(res[k]["SOS"])
    if m.sum() < 10:
        continue
    e = [np.median(res[k]["EOS"][m]) for k in L]; s = [np.median(res[k]["SOS"][m]) for k in L]
    pe = [100 * np.mean(res[k]["pE"][m] < 0.05) for k in L]
    out.append("%-7s %5d | %+5.2f %+5.2f %+5.2f (sig %2.0f/%2.0f/%2.0f%%) | %+5.2f %+5.2f %+5.2f" % (name, m.sum(), *e, *pe, *s))
open("../data/s8_eos_temp_sensitivity.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
