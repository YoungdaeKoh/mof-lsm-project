#!/usr/bin/env python3
"""Step 2: double-logistic fits to regional LAI series at native sampling, 2001-2015.

Products: GLASS 8-day, GIMMS-cons half-monthly, GIMMS-AVHRR half-monthly (../data/obs_native, o1), CTRL monthly
(poster data). Regions: boreal 50-70N land and the latitude bands of Fig. 1d-e; cells valid in all products' monthly
files (same mask as Fig. 1), cos-lat weights.
Per region and product: one fit per year (samples of that year), SOS/EOS at 50 % of the fitted amplitude, mean and sd
over years; and a fit to the 15-yr mean curve. Sampling test: GLASS fitted at 8-day vs GLASS monthly means -> how much
the monthly sampling moves the dates (the uncertainty that applies to CTRL, which is monthly only).
output: ../data/o2_regional_fit_native.txt
"""
import warnings
import datetime as dt
import numpy as np
import netCDF4 as nc
import regionmask
import dlog

P = "../../../poster/2026_LM4p_LAI/data/"; N = "../data/obs_native/"
A, B = 2001, 2015; NY = B - A + 1
MON = {"GIMMS": (P + "gimms_lai_mon_1982_2020.nc", 1982), "AVHRR": (P + "gimms_solely_lai_mon_1982_2015.nc", 1982),
       "GLASS": (P + "glass_lai_modis_monthly_1deg_2001_2020.nc", 2001), "CTRL": (P + "lm4p_ctl_lai_mon_1982_2020.nc", 1982)}
NAT = {"GLASS": N + "glass_1deg_2001_2015.nc", "GIMMS": N + "cons_1deg_2001_2015.nc", "AVHRR": N + "solely_1deg_2001_2015.nc"}
MID = np.array([15.5, 45, 74.5, 105, 135.5, 166, 196.5, 227.5, 258, 288.5, 319, 349.5])


def readm(fn, y0):
    with nc.Dataset(fn) as d:
        n = [v for v in d.variables if d.variables[v].ndim == 3][0]
        v = np.ma.filled(d[n][(A - y0) * 12:(B - y0 + 1) * 12].astype("f8"), np.nan)
    v[np.abs(v) > 100] = np.nan
    return v


mon = {k: readm(*MON[k]) for k in MON}
ok = np.all([np.isfinite(v).all(0) for v in mon.values()], 0)
nat = {}
for k, fn in NAT.items():
    with nc.Dataset(fn) as d:
        t = d["time"][:].astype(float); x = np.ma.filled(d["lai"][:].astype("f8"), np.nan)
    x[np.abs(x) > 100] = np.nan
    yr = np.array([(dt.date(A, 1, 1) + dt.timedelta(int(tt))).year for tt in t])
    doy = np.array([(dt.date(A, 1, 1) + dt.timedelta(int(tt)) - dt.date(y, 1, 1)).days + 1 for tt, y in zip(t, yr)])
    nat[k] = (yr, doy, x)
lat = -89.5 + np.arange(180); lon = -179.5 + np.arange(360)
W = np.cos(np.radians(lat))[:, None] * np.ones((1, 360))
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    land = regionmask.defined_regions.ar6.land.mask_3D(lon, lat).values.any(0)
REG = {"50-70N": (50, 70), "20-40N": (20, 40), "40-50N": (40, 50), "50-60N": (50, 60), "60-70N": (60, 70)}


def series(x, w):
    return np.array([np.nansum(x[t] * w) / w.sum() for t in range(x.shape[0])])


def yearly_dates(t_all, y_all, yr_all):
    res = []
    for y in range(A, B + 1):
        s = yr_all == y
        p = dlog.fit(t_all[s], y_all[s])
        res.append([dlog.dates(p)[k] for k in ("sos50", "eos50")] if p is not None else [np.nan, np.nan])
    return np.array(res)


out = ["Double-logistic SOS/EOS (50 %% of fitted amplitude), %d-%d, regional cos-lat means; yearly fits: mean +- sd over years | fit to the 15-yr mean curve" % (A, B)]
for rn, (a, b) in REG.items():
    w = W * (ok & land & ((lat >= a) & (lat < b))[:, None])
    out += ["", "%s (%d cells)" % (rn, int((w > 0).sum())), "%-14s | %6s %5s  %6s %5s | %6s %6s | %s" % ("product", "SOS", "sd", "EOS", "sd", "SOSclim", "EOSclim", "sampling")]
    rows = {}
    for k in ("GLASS", "GIMMS", "AVHRR"):
        yr, doy, x = nat[k]; ts = series(x, w)
        yd = yearly_dates(doy.astype(float), ts, yr)
        clim_t = doy[yr == A].astype(float); clim = np.array([ts[yr == y] for y in range(A, B + 1)])
        clim = clim.mean(0) if all(len(c) == len(clim[0]) for c in clim) else None
        pc = dlog.fit(clim_t, clim) if clim is not None else None
        dc = dlog.dates(pc) if pc is not None else {"sos50": np.nan, "eos50": np.nan}
        rows[k] = yd
        out.append("%-14s | %6.1f %5.1f  %6.1f %5.1f | %6.1f %6.1f | native %s" % (k + " native", np.nanmean(yd[:, 0]), np.nanstd(yd[:, 0]), np.nanmean(yd[:, 1]), np.nanstd(yd[:, 1]), dc["sos50"], dc["eos50"], "8-day" if k == "GLASS" else "half-month"))
    for k in ("GLASS", "GIMMS", "AVHRR", "CTRL"):
        ts = series(mon[k], w).reshape(NY, 12)
        yd = yearly_dates(np.tile(MID, NY), ts.ravel(), np.repeat(np.arange(A, B + 1), 12))
        pc = dlog.fit(MID, ts.mean(0)); dc = dlog.dates(pc)
        tag = "monthly"
        if k in rows:
            tag += "  (native - monthly: SOS %+.1f, EOS %+.1f d)" % (np.nanmean(rows[k][:, 0]) - np.nanmean(yd[:, 0]), np.nanmean(rows[k][:, 1]) - np.nanmean(yd[:, 1]))
        out.append("%-14s | %6.1f %5.1f  %6.1f %5.1f | %6.1f %6.1f | %s" % (k + " monthly", np.nanmean(yd[:, 0]), np.nanstd(yd[:, 0]), np.nanmean(yd[:, 1]), np.nanstd(yd[:, 1]), dc["sos50"], dc["eos50"], tag))
        rows[k + "_m"] = yd
    o = np.array([np.nanmean(rows[k], 0) for k in ("GLASS", "GIMMS", "AVHRR")]); c = np.nanmean(rows["CTRL_m"], 0)
    out.append("CTRL - obs(native) mean: SOS %+.1f (obs spread %.1f)  EOS %+.1f (obs spread %.1f)" % (c[0] - o[:, 0].mean(), np.ptp(o[:, 0]), c[1] - o[:, 1].mean(), np.ptp(o[:, 1])))
open("../data/o2_regional_fit_native.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
