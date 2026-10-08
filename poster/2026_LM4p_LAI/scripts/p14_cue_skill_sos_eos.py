#!/usr/bin/env python3
"""Which single environmental cue best predicts the observed SOS and EOS? (spatial, climatological test)

Observed: GIMMS LAI4g 1982-2010 climatology, 1-deg cells 20-75N with amplitude >= 0.5; SOS / EOS = 50 % amplitude
crossings before / after the peak of the daily-interpolated monthly curve (same definition as the poster).
Temperature: ERA5 monthly 2-m temperature 1982-2010 climatology (0.25 deg NH, lat descending, lon 0-360) averaged
onto the 1-deg GIMMS cells and interpolated to days. Day length: Cooper declination + sunrise equation at the cell latitude.
Chilling: days with 0 <= T <= 5 C from 1 Nov to the date (climatological daily T). GDD: sum of max(T - 5 C, 0) from 1 Jan.
Each cue rule has 1-3 constants fitted once for all cells (grid search, cos-lat weighted RMSE of predicted - observed date).
Spring rules:  DL  first day DL >= X | T  first day T >= T* | GDD  first day GDD >= G
               GDD+chill  GDD >= a + b*exp(-c*chill) (Murray et al. 1989 form) | GDD+DL  GDD >= G and DL >= X
Autumn rules (after the observed peak):  DL  first day DL < X | T  first day T < T* | DL+T  DL < X and T < T*
Caveat: space-for-time (one climatological date per cell); interannual skill needs yearly SOS/EOS (VIPPHEN, next step).
output: ../data/cue_skill_sos_eos.txt
"""
import itertools
import numpy as np
import netCDF4 as nc

D = np.arange(1, 366.0)
MID = np.array([15.5, 45, 74.5, 105, 135.5, 166, 196.5, 227.5, 258, 288.5, 319, 349.5])


def to_daily(m):        # cyclic linear interpolation of 12 monthly values to 365 days (last axis = month)
    x = np.concatenate([MID - 365, MID, MID + 365]); y = np.concatenate([m, m, m], axis=-1)
    return np.apply_along_axis(lambda v: np.interp(D, x, v), -1, y)


# ---- observations
g = nc.Dataset("../data/gimms_lai_clim_1982_2010.nc")
clim = np.ma.filled(g["clim"][:].astype("f8"), np.nan); lat = np.asarray(g["lat"][:]); lon = np.asarray(g["lon"][:])
ok = np.isfinite(clim).all(0) & (lat[:, None] > 20) & (lat[:, None] < 75) & ((clim.max(0) - clim.min(0)) >= 0.5)

# ---- ERA5 t2m 1982-2010 monthly climatology -> 1-deg cells (block mean of 4x4 0.25-deg points)
e = nc.Dataset("/Volumes/data02/ERA5/ERA5m_t2m_NH_1979-2023.nc")
elat = np.asarray(e["latitude"][:]); elon = np.asarray(e["longitude"][:])
assert elat[0] > elat[-1] and elon.min() >= 0, "unexpected ERA5 grid orientation"
t0 = (1982 - 1979) * 12
T = np.asarray(e["t2m"][t0:t0 + 29 * 12], "f4").reshape(29, 12, elat.size, elon.size).mean(0) - 273.15
Tc = np.full((12, 180, 360), np.nan)
for i in np.where((lat > 20) & (lat < 75))[0]:
    li = (elat >= lat[i] - 0.5) & (elat < lat[i] + 0.5)
    for j in range(360):
        lo = lon[j] % 360
        lj = (elon >= lo - 0.5) & (elon < lo + 0.5)
        Tc[:, i, j] = T[:, li][:, :, lj].mean(axis=(1, 2))
print("ERA5 check: mean Jan / Jul T over 50-60N land cells %.1f / %.1f C" % (
    np.nanmean(Tc[0][(lat[:, None] > 50) & (lat[:, None] < 60) & ok]), np.nanmean(Tc[6][(lat[:, None] > 50) & (lat[:, None] < 60) & ok])))

cells = list(zip(*np.where(ok & np.isfinite(Tc).all(0))))
n = len(cells)
LAT = np.array([lat[i] for i, j in cells]); W = np.cos(np.radians(LAT))
LAId = to_daily(np.array([clim[:, i, j] for i, j in cells]))
Td = to_daily(np.array([Tc[:, i, j] for i, j in cells]))
decl = 0.409 * np.sin(2 * np.pi * (284 + D) / 365)
DL = 24 / np.pi * np.arccos(np.clip(-np.tan(np.radians(LAT))[:, None] * np.tan(decl)[None, :], -1, 1))

sos = np.full(n, np.nan); eos = np.full(n, np.nan); pk = np.argmax(LAId, 1)
for k in range(n):
    v = LAId[k]; half = v.min() + 0.5 * (v.max() - v.min())
    up = np.where((v[:pk[k]] < half) & (np.roll(v, -1)[:pk[k]] >= half))[0]
    dn = np.where((v[pk[k]:] >= half) & (np.roll(v, -1)[pk[k]:] < half))[0]
    if up.size: sos[k] = up[-1] + 1
    if dn.size: eos[k] = pk[k] + dn[0] + 1
gdd = np.cumsum(np.maximum(Td - 5, 0), 1)
# chilling: days 0..5 C counted from 1 Nov of the previous year (climatology wraps) up to each day
cold = ((Td >= 0) & (Td <= 5)).astype(float)
chill = np.cumsum(np.concatenate([cold[:, 304:], cold], 1), 1)[:, 365 - 304 - 1 + 1:][:, :365]


def first(mask, start=None):
    """first day index (1-based) where mask is true, optionally only from start (per cell); nan if never"""
    m = mask.copy()
    if start is not None:
        m &= (np.arange(365)[None, :] >= start[:, None])
    idx = np.where(m.any(1), m.argmax(1) + 1, np.nan)
    return idx


def score(pred, obs, sel):
    s = sel & np.isfinite(pred) & np.isfinite(obs)
    return np.sqrt(np.sum(W[s] * (pred[s] - obs[s]) ** 2) / np.sum(W[s])), s.sum() / max(sel.sum(), 1)


def fit(rule, grids, obs, sel):
    best = (np.inf, None, 0)
    for p in itertools.product(*grids):
        r, cov = score(rule(*p), obs, sel)
        if cov > 0.9 and r < best[0]:
            best = (r, p, cov)
    return best


before = np.arange(365)[None, :] < pk[:, None]
after_pk = pk
spring = {
    "DL": (lambda X: first((DL >= X) & before), [np.arange(9, 20.01, 0.25)]),
    "T": (lambda Ts: first((Td >= Ts) & before), [np.arange(-5, 20.01, 0.5)]),
    "GDD": (lambda G: first((gdd >= G) & before), [np.arange(0, 600, 10)]),
    "GDD+chill": (lambda a, b, c: first((gdd >= a + b * np.exp(-c * chill)) & before),
                  [np.arange(0, 400, 25), np.arange(0, 1200, 100), [0.005, 0.01, 0.02, 0.04, 0.08]]),
    "GDD+DL": (lambda G, X: first((gdd >= G) & (DL >= X) & before), [np.arange(0, 400, 20), np.arange(10, 17.01, 0.5)]),
}
autumn = {
    "DL": (lambda X: first((DL < X), after_pk), [np.arange(9, 18.01, 0.25)]),
    "T": (lambda Ts: first((Td < Ts), after_pk), [np.arange(-5, 22.01, 0.5)]),
    "DL+T": (lambda X, Ts: first((DL < X) & (Td < Ts), after_pk), [np.arange(9, 17.01, 0.5), np.arange(0, 22.01, 1)]),
}
bands = [("20-75N", (LAT > 20)), ("50-75N", LAT >= 50), ("40-50N", (LAT >= 40) & (LAT < 50)), ("20-40N", LAT < 40)]
out = [__doc__.split("\n")[1], "cells %d (SOS defined %d, EOS defined %d); RMSE in days (cos-lat weighted); constants fitted on all cells" % (
    n, np.isfinite(sos).sum(), np.isfinite(eos).sum()), ""]
for name, obs, rules in (("SOS", sos, spring), ("EOS", eos, autumn)):
    out.append("=== %s (observed median doy %.0f)" % (name, np.nanmedian(obs)))
    out.append("  %-10s %-28s %8s | %s" % ("cue", "fitted constants", "RMSE all", "  ".join("%s" % b for b, _ in bands[1:])))
    for cue, (rule, grids) in rules.items():
        r, p, cov = fit(rule, grids, obs, np.isfinite(obs))
        pred = rule(*p)
        rb = ["%6.1f" % score(pred, obs, np.isfinite(obs) & m)[0] for _, m in bands[1:]]
        out.append("  %-10s %-28s %8.1f | %s   (coverage %.0f %%)" % (cue, ", ".join("%g" % v for v in p), r, "  ".join(rb), 100 * cov))
    out.append("")
# spread of each cue's value at the observed date (how tightly it clusters)
for name, obs in (("SOS", sos), ("EOS", eos)):
    s = np.isfinite(obs); idx = (obs[s] - 1).astype(int); rows = np.where(s)[0]
    q = lambda v: "median %6.1f  p10-p90 %6.1f..%6.1f" % (np.median(v), np.percentile(v, 10), np.percentile(v, 90))
    out.append("%s: day length %s h | T %s C | GDD %s | chill days %s" % (name, q(DL[rows, idx]), q(Td[rows, idx]), q(gdd[rows, idx]), q(chill[rows, idx])))
open("../data/cue_skill_sos_eos.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
