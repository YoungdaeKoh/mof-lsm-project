#!/usr/bin/env python3
"""How uncertain are observed SOS/EOS/LOS? Three satellite LAI products vs LM4p ctl, same years, same method.

Products (monthly, 1 deg, same grid): GIMMS LAI4g consolidated (AVHRR to 2003, reprocessed MODIS from 2004; Cao et al. 2023),
GIMMS LAI4g solely (AVHRR only, to 2015), GLASS LAI V61 MODIS (p23), LM4p ctl (WFDE5, CO2 fixed).
Periods: A 2001-2015 (all four), B 2001-2020 (without GIMMS solely).
Method = p3_regional_seasonal_sos_eos.py: regional mean over cells valid in every month of every product in the period,
cos-lat weights, monthly means at mid-month linearly interpolated to days, per-year threshold min + THR*(max-min);
SOS = last upward crossing before the peak, EOS = first downward crossing after it, LOS = EOS - SOS. THR 0.2 and 0.5.
Obs spread = max - min of the observational products' mean dates; the model is "outside" when it is further from the
nearest product than that spread... reported as model - obs mean and model - nearest product.
Output: ../data/sos_eos_three_obs.txt
"""
import warnings
import numpy as np
import netCDF4 as nc
import regionmask

MID = np.array([15.5, 45.0, 74.5, 105.0, 135.5, 166.0, 196.5, 227.5, 258.0, 288.5, 319.0, 349.5])
DOY = np.arange(1, 366)
FILES = {"GIMMS-cons": ("../data/gimms_lai_mon_1982_2020.nc", 1982), "GIMMS-AVHRR": ("../data/gimms_solely_lai_mon_1982_2015.nc", 1982),
         "GLASS-MODIS": ("../data/glass_lai_modis_monthly_1deg_2001_2020.nc", 2001), "LM4p": ("../data/lm4p_ctl_lai_mon_1982_2020.nc", 1982)}


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
REG = {c: m3.sel(region=ar6.map_keys(c)).values.astype(bool) for c in ("NEU", "RFE", "NWN", "ESB", "WSB", "NEN")}
REG["50-70N land"] = m3.values.any(0) & ((lat >= 50) & (lat <= 70))[:, None]

out = ["SOS/EOS/LOS (day of year) from three satellite LAI products and LM4p ctl; regional means over common valid cells",
       "obs spread = max-min of the obs products; dM = LM4p - obs mean; dN = LM4p - nearest obs product (0 if inside the obs range)", ""]
for (a, b, prods) in ((2001, 2015, ("GIMMS-cons", "GIMMS-AVHRR", "GLASS-MODIS", "LM4p")), (2001, 2020, ("GIMMS-cons", "GLASS-MODIS", "LM4p"))):
    ny = b - a + 1
    data = {p: read(FILES[p][0], FILES[p][1], a, b) for p in prods}
    ok = np.all([np.isfinite(v).all(0) for v in data.values()], 0)
    for thr in (0.2, 0.5):
        out.append("=== %d-%d, threshold %d %%, products: %s" % (a, b, round(100 * thr), ", ".join(prods)))
        out.append("%-12s %5s | %-6s" % ("region", "cells", "metric") + "".join("%13s" % p for p in prods) + " | obs spread    dM    dN")
        for rn, rm in REG.items():
            w = W * (rm & ok)
            if w.sum() == 0:
                continue
            res = {}
            for p in prods:
                ts = np.array([np.nansum(data[p][t] * w) / w.sum() for t in range(ny * 12)]).reshape(ny, 12)
                st = []
                for y in range(ny):
                    pd = ts[y - 1, 11] if y > 0 else ts[y, 11]; nj = ts[y + 1, 0] if y < ny - 1 else ts[y, 0]
                    c = np.interp(DOY, np.concatenate([[MID[-1] - 365], MID, [MID[0] + 365]]), np.concatenate([[pd], ts[y], [nj]]))
                    st.append(sos_eos(c, thr))
                st = np.array(st); res[p] = {"SOS": np.nanmean(st[:, 0]), "EOS": np.nanmean(st[:, 1]), "LOS": np.nanmean(st[:, 1] - st[:, 0])}
            for k in ("SOS", "EOS", "LOS"):
                ob = np.array([res[p][k] for p in prods if p != "LM4p"]); mdl = res["LM4p"][k]
                dn = 0.0 if ob.min() <= mdl <= ob.max() else (mdl - ob.max() if mdl > ob.max() else mdl - ob.min())
                out.append("%-12s %5d | %-6s" % (rn if k == "SOS" else "", int((rm & ok).sum()), k) + "".join("%13.1f" % res[p][k] for p in prods)
                           + " | %10.1f %+5.1f %+5.1f" % (ob.max() - ob.min(), mdl - ob.mean(), dn))
        out.append("")
open("../data/sos_eos_three_obs.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
