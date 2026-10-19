#!/usr/bin/env python3
"""SOS/EOS 2010 against three observed LAI products: is the model's spring bias the same whichever product we use?

Same method as p8 (monthly LAI interpolated to days, SOS = 50 % amplitude upward crossing before the peak),
same cells (north of 20N, GIMMS 2010 amplitude >= 0.5), additionally finite in every product.
Obs: GIMMS LAI4g consolidated (MODIS-reprocessed from 2004), GIMMS AVHRR-only, GLASS V61 MODIS (all 1 deg, same grid).
Models: CTRL (base) and DL13/12 (dayl, spring rules = CTRL) from ../data/<run>.lai.2010-2010.1deg.nc.
output: ../data/sos_2010_three_obs.txt (SOS and EOS tables; AR6 regions, cos-lat weighted, + = model later)
"""
import numpy as np
import netCDF4 as nc
import regionmask

YEAR = 2010
D = np.arange(1, 366.0)
MID = np.array([15.5, 45, 74.5, 105, 135.5, 166, 196.5, 227.5, 258, 288.5, 319, 349.5])
OBS = [("GIMMS", "gimms_lai_mon_1982_2020.nc", 1982), ("AVHRR", "gimms_solely_lai_mon_1982_2015.nc", 1982),
       ("GLASS", "glass_lai_modis_monthly_1deg_2001_2020.nc", 2001)]
RUNS = [("CTRL", "base"), ("DL13/12", "dayl")]

fields = {}
for name, f, y0 in OBS:
    with nc.Dataset("../data/" + f) as A:
        i0 = (YEAR - y0) * 12
        fields[name] = np.ma.filled(A["lai"][i0:i0 + 12].astype("f8"), np.nan)
        lat = np.asarray(A["lat"][:]); lon = np.asarray(A["lon"][:])
for name, key in RUNS:
    with nc.Dataset("../data/%s.lai.%d-%d.1deg.nc" % (key, YEAR, YEAR)) as A:
        fields[name] = np.ma.filled(A["lai"][:].astype("f8"), np.nan)

ok = (lat[:, None] >= 20) & np.ones((1, lon.size), bool)
for v in fields.values():
    ok &= np.isfinite(v).all(0)
ok &= (fields["GIMMS"].max(0) - fields["GIMMS"].min(0)) >= 0.5


def dates(m):
    c = np.interp(D, np.r_[MID[-1] - 365, MID, MID[0] + 365], np.r_[m[-1], m, m[0]])
    thr = c.min() + 0.5 * (c.max() - c.min()); ip = int(c.argmax())
    up = [k for k in range(ip) if c[k] < thr <= c[k + 1]]
    dn = [k for k in range(ip, 364) if c[k] >= thr > c[k + 1]]
    s = D[up[-1]] + (thr - c[up[-1]]) / (c[up[-1] + 1] - c[up[-1]]) if up else np.nan
    e = D[dn[0]] + (c[dn[0]] - thr) / (c[dn[0]] - c[dn[0] + 1]) if dn else np.nan
    return s, e


sos = {k: np.full(ok.shape, np.nan) for k in fields}; eos = {k: np.full(ok.shape, np.nan) for k in fields}
for i, j in zip(*np.where(ok)):
    for k, v in fields.items():
        sos[k][i, j], eos[k][i, j] = dates(v[:, i, j])

W = np.cos(np.radians(lat))[:, None] * np.ones((1, lon.size))
reg = regionmask.defined_regions.ar6.land.mask(lon, lat).values
obs = [o[0] for o in OBS]
out = []
for name, dd in (("SOS", sos), ("EOS", eos)):
    out += ["%s %d (50 %% amplitude, monthly interpolated), cos-lat weighted, days; obs columns = day of year, model columns = model - obs" % (name, YEAR),
            "%-8s %5s | %6s %6s %6s %6s | %-24s | %-24s" % ("region", "cells", *obs, "range", "CTRL - G/A/GL", "DL13/12 - G/A/GL")]
    for code in ("50-70N", "NEU", "RFE", "NWN", "ESB", "NEN", "WSB", "RAR", "EEU", "WCE", "ENA", "EAS",
                 "WSB45-55", "WSB55-65", "ESB45-55", "ESB55-65"):
        if code == "50-70N":
            m = ok & (lat[:, None] >= 50) & (lat[:, None] < 70)
        else:   # "WSB45-55" = WSB cells in the 45-55N band (steppe/forest-steppe vs taiga)
            m = ok & (reg == regionmask.defined_regions.ar6.land.map_keys(code[:3]))
            if len(code) > 3:
                b0, b1 = map(int, code[3:].split("-")); m &= (lat[:, None] >= b0) & (lat[:, None] < b1)
        for v in dd.values():
            m &= np.isfinite(v)
        if m.sum() < 10:
            continue
        wm = lambda a: np.sum(a[m] * W[m]) / W[m].sum()
        o = [wm(dd[k]) for k in obs]
        out.append("%-8s %5d | %6.1f %6.1f %6.1f %6.1f | %+6.1f %+6.1f %+6.1f     | %+6.1f %+6.1f %+6.1f" % (
            code, m.sum(), *o, max(o) - min(o), *[wm(dd["CTRL"]) - x for x in o], *[wm(dd["DL13/12"]) - x for x in o]))
    out.append("")
open("../data/sos_2010_three_obs.txt", "w").write("\n".join(out) + "\n"); print("\n".join(out))
