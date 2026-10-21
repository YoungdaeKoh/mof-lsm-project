#!/usr/bin/env python3
"""Full-year daylspring5_d (DL13/12 autumn + spring 5-day smoothing with the leaf-off fix): SOS/EOS and seasonal LAI
against three observed LAI products, next to CTRL (base) and DL13/12 (dayl).

Same method and cells as p25 (monthly LAI interpolated to days, 50 % amplitude crossings, north of 20N,
GIMMS 2010 amplitude >= 0.5, finite in every field), AR6 regions, cos-lat weighted.
Also: May-Jun and Sep-Oct mean LAI and the 12-month MAE against GIMMS per region (does the spring change spill
into summer/autumn?).
input: ../data/{base,dayl,daylspring5}.lai.2010-2010.1deg.nc (daylspring5 = 1-deg of phentest_2010/daylspring5_full_d)
output: ../data/daylspring5_2010.txt
"""
import os
import numpy as np
import netCDF4 as nc
import regionmask

YEAR = 2010
D = np.arange(1, 366.0)
MID = np.array([15.5, 45, 74.5, 105, 135.5, 166, 196.5, 227.5, 258, 288.5, 319, 349.5])
OBS = [("GIMMS", "gimms_lai_mon_1982_2020.nc", 1982), ("AVHRR", "gimms_solely_lai_mon_1982_2015.nc", 1982),
       ("GLASS", "glass_lai_modis_monthly_1deg_2001_2020.nc", 2001)]
RUNS = [("CTRL", "base"), ("DL", "dayl"), ("DLS5", "daylspring5"), ("DLH5", "daylhold5"),
        ("DLLAT", "dayllat")]   # DLH5 = DLS5 + spring 12 h floor; DLLAT = autumn 12.0 + 0.05(|lat|-40) h, spring CTRL
RUNS = [r for r in RUNS if os.path.exists("../data/%s.lai.%d-%d.1deg.nc" % (r[1], YEAR, YEAR))]
REGIONS = ("50-70N", "40-50N", "NEU", "RFE", "NWN", "ESB", "NEN", "WSB", "RAR", "EEU", "WCE", "ENA", "EAS", "TIB")

fields = {}
for name, f, y0 in OBS:
    with nc.Dataset("../data/" + f) as A:
        i0 = (YEAR - y0) * 12
        fields[name] = np.ma.filled(A["lai"][i0:i0 + 12].astype("f8"), np.nan)
        lat = np.asarray(A["lat"][:]); lon = np.asarray(A["lon"][:])
for name, key in RUNS:
    with nc.Dataset("../data/%s.lai.%d-%d.1deg.nc" % (key, YEAR, YEAR)) as A:
        assert np.allclose(A["lat"][:], lat) and np.allclose(A["lon"][:], lon)
        fields[name] = np.ma.filled(A["lai"][:].astype("f8"), np.nan)
fields = {k: np.where(np.abs(v) > 100, np.nan, v) for k, v in fields.items()}

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
LA = lat[:, None] * np.ones((1, lon.size))


def region(code):
    if code[0].isdigit():
        b0, b1 = map(int, code[:-1].split("-")); return ok & (LA >= b0) & (LA < b1)
    return ok & (reg == regionmask.defined_regions.ar6.land.map_keys(code))


obs = [o[0] for o in OBS]; runs = [r[0] for r in RUNS]
out = []
for name, dd in (("SOS", sos), ("EOS", eos)):
    out += ["%s %d, cos-lat weighted; obs = mean doy of GIMMS/AVHRR/GLASS (range); model columns = model - obs mean (days)" % (name, YEAR),
            "%-7s %5s | %6s %5s | " % ("region", "cells", "obs", "range") + " ".join("%6s" % r for r in runs) + " | DLS5-DL"]
    for code in REGIONS:
        m = region(code)
        for v in dd.values():
            m = m & np.isfinite(v)
        if m.sum() < 10:
            continue
        wm = lambda a: np.sum(a[m] * W[m]) / W[m].sum()
        o = [wm(dd[k]) for k in obs]; om = np.mean(o)
        b = [wm(dd[r]) - om for r in runs]
        out.append("%-7s %5d | %6.1f %5.1f | " % (code, m.sum(), om, max(o) - min(o)) + " ".join("%+6.1f" % x for x in b) + " | %+6.1f" % (b[2] - b[1]))
    out.append("")

out += ["Seasonal LAI vs GIMMS 2010 (m2/m2): May-Jun mean, Sep-Oct mean, 12-month MAE; same cells",
        "%-7s | MJ obs %s | SO obs %s | MAE %s" % ("region", " ".join(runs), " ".join(runs), " ".join(runs))]
for code in REGIONS:
    m = region(code)
    wm = lambda a: np.sum(a[:, m] * W[m], 1) / W[m].sum()
    c = {k: wm(fields[k]) for k in ["GIMMS"] + runs}
    mj = [c[k][4:6].mean() for k in ["GIMMS"] + runs]; so = [c[k][8:10].mean() for k in ["GIMMS"] + runs]
    mae = [np.mean(np.abs(c[r] - c["GIMMS"])) for r in runs]
    f2 = lambda a: " ".join("%4.2f" % x for x in a)
    out.append("%-7s | %s | %s | %s" % (code, f2(mj), f2(so), f2(mae)))
open("../data/daylspring5_2010.txt", "w").write("\n".join(out) + "\n"); print("\n".join(out))
