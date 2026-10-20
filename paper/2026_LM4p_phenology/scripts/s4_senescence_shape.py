#!/usr/bin/env python3
"""Autumn LAI decline: does the model differ from observations in WHEN the decline starts or HOW FAST it falls?

Obs: GLASS V61 8-day (o1, 1 deg) for 2010 and the 2001-2015 mean, linearly interpolated to days.
Model: DL13/12 run (dayl_d, daily LAI, C96 binned to 1 deg; CTRL has no daily LAI). Year 2010.
Groups: latitude band x CTRL-dominant species (>= 50 % July leaf area, p9 map), cells with GLASS 2010 amplitude
>= 0.5 and model amplitude >= 0.3; cos-lat weighted mean curves.
Metrics on each mean curve (after the annual peak): days at 90 / 50 / 10 % of amplitude, the fall time 90->10 %,
and a hinge-exponential fit L = Lpk (t < t0), Lmin + (Lpk - Lmin) exp(-k (t - t0)) (t >= t0) from the peak to doy 365:
t0 = decline start, k = daily loss rate (half-life ln2/k).
output: ../data/s4_senescence_shape.txt
"""
import glob
import datetime as dt
import numpy as np
from netCDF4 import Dataset
from scipy.optimize import curve_fit

D = np.arange(1, 366)
lat = np.arange(-89.5, 90, 1.0)
with Dataset("data/obs_native/glass_1deg_2001_2015.nc") as A:
    t = A["time"][:].astype(float); x = np.ma.filled(A["lai"][:].astype("f8"), np.nan)
    assert np.allclose(A["lat"][:], lat)
x[np.abs(x) > 100] = np.nan
day = [dt.date(2001, 1, 1) + dt.timedelta(int(v)) for v in t]
yr = np.array([d.year for d in day]); doy = np.array([d.timetuple().tm_yday for d in day])


def to_daily(sel):
    """8-day series of selected samples -> daily (365, 180, 360) by linear interpolation in time."""
    s = np.argsort(doy[sel]); dd = doy[sel][s]; v = x[sel][s]
    out = np.empty((365, 180, 360))
    for i in range(180):
        for j in range(360):
            out[:, i, j] = np.interp(D, np.r_[dd[-1] - 365, dd, dd[0] + 365], np.r_[v[-1, i, j], v[:, i, j], v[0, i, j]])
    return out


g10 = to_daily(yr == 2010)
gcl = np.nanmean(np.array([to_daily(yr == y) for y in range(2001, 2016)]), 0)

# model daily LAI, C96 -> 1 deg mean
num = np.zeros((365, 180, 360)); den = np.zeros((180, 360))
for f in sorted(glob.glob("/Volumes/data02/LM4P/cases/phentest_2010/dayl_d/20100101.land_daily.tile*.nc")):
    with Dataset(f) as A:
        A.set_auto_mask(False)
        la = A["geolat_t"][:].ravel(); lo = A["geolon_t"][:].ravel(); lo = np.where(lo > 180, lo - 360, lo)
        v = A["lai"][:].astype("f8").reshape(365, -1)
    ok = np.all((v >= 0) & (v < 1e10), 0)
    ci = np.clip(((la + 90) // 1).astype(int), 0, 179)[ok]; cj = np.clip(((lo + 180) // 1).astype(int), 0, 359)[ok]
    np.add.at(den, (ci, cj), 1.0)
    for d in range(365):
        np.add.at(num[d], (ci, cj), v[d, ok])
mod = np.where(den > 0, num / np.where(den > 0, den, 1), np.nan)

z = np.load("../../poster/2026_LM4p_LAI/data/model_species_dominance_1deg_2010.npz", allow_pickle=True)
names = list(z["species"]); share = z["share"]
LA = lat[:, None] * np.ones((1, 360)); W = np.cos(np.radians(LA))
base = (np.nanmax(g10, 0) - np.nanmin(g10, 0) >= 0.5) & (np.nanmax(mod, 0) - np.nanmin(mod, 0) >= 0.3) & np.isfinite(g10).all(0) & np.isfinite(mod).all(0)


def hinge(tt, t0, k, lpk, lmin):
    return np.where(tt < t0, lpk, lmin + (lpk - lmin) * np.exp(-k * np.clip(tt - t0, 0, None)))


def metrics(c):
    ip = int(np.argmax(c[:300])); lo_ = c[ip:].min(); amp = c[ip] - lo_
    cross = lambda f: next((D[ip + n] for n in range(365 - ip) if c[ip + n] <= lo_ + f * amp), np.nan)
    tt = D[ip:].astype(float); yy = c[ip:]
    try:
        p, _ = curve_fit(hinge, tt, yy, p0=(D[ip] + 20, 0.05, c[ip], lo_), bounds=([D[ip], 0.002, 0, 0], [360, 1.0, 10, 10]))
    except RuntimeError:
        p = (np.nan,) * 4
    return D[ip], cross(0.9), cross(0.5), cross(0.1), p[0], p[1]


out = ["Autumn decline shape: GLASS 2010 / GLASS 2001-15 mean / model DL13/12 2010 (doy; k in %/day, half-life in days)",
       "%-22s %-9s %5s | %4s %4s %4s %4s %6s | %6s %5s %5s" % ("group", "curve", "n", "peak", "90%", "50%", "10%", "90-10", "t0", "k", "t1/2")]
for a, b in ((40, 50), (50, 60), (60, 70)):
    for sp in ("c3grass", "acer", "picea"):
        m = base & (LA >= a) & (LA < b) & (share[names.index(sp)] >= 0.5)
        if m.sum() < 15:
            continue
        w = W[m]
        for lab, F in (("GLASS2010", g10), ("GLASSclim", gcl), ("DL13/12", mod)):
            c = (F[:, m] * w).sum(1) / w.sum()
            pk, c9, c5, c1, t0, k = metrics(c)
            out.append("%-22s %-9s %5d | %4d %4.0f %4.0f %4.0f %6.0f | %6.0f %5.1f %5.1f" % ("%d-%dN %s" % (a, b, sp), lab, m.sum(), pk, c9, c5, c1, c1 - c9, t0, 100 * k, np.log(2) / k))
        out.append("")
open("data/s4_senescence_shape.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
