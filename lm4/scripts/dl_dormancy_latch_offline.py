#!/usr/bin/env python3
"""Offline test of a dormancy latch for the autumn day-length rule (c3grass parameters), dayl_d 2010 daily temperatures.

Problem (findings 2026-10-19): after the local winter solstice `shortening` is false, the day-length leaf-off no longer
holds, and in mild winters (tc_pheno >= 5 C, GDD 180 reached quickly) leaves switch on again (SH July LAI 1.48 -> 1.85,
obs minimum 0.96; NH 20-40N January LAI 1.60 vs obs 0.75 already in CTRL).
Leaf state machine per cell, one step per day (vegn_dynamics.F90 vegn_phenology_ppa + DL patch, drought ignored):
  OFF -> ON : gdd > 180 and tc >= 5 C and latch released
  ON -> OFF : tc < 5 C  or  (shortening and dayl < 13 h and tc < 20 C);  gdd reset to 0 at leaf-off
  gdd accumulates daily (Tmax, Tmin above 0 C, as spring_gate_diag.py), tc = 20-day EMA of canopy Tmean
Candidates for the latch (set by any leaf-off, released when):
  CUR   no latch (current patch)
  EQ12  days lengthening and dayl >= 12 h (after the local spring equinox)
  EQ11  days lengthening and dayl >= 11 h
  SOL60 60 days after the local winter solstice
  SOL30 30 days after the local winter solstice
  HOLD12 stateless (no latch variable, restart-safe): leaf-on also needs NOT (dayl < 12 h and tc < 20 C)
Year 2010 run twice, statistics from the second pass (initial state from the first).
Per band: % cells with a leaf-on within 60 days after the local winter solstice ("winter re-greening"),
median first leaf-on after the solstice (days after solstice), and observed SOS (GIMMS 2010, 50 % amplitude, nearest
1-deg cell; SH series shifted by half a year) in the same units. Model LAI 50 % comes ~8 d after leaf-on (findings 10-19).
Cells: C96 with dayl_d LAI range > 0.3.
usage: python3 dl_dormancy_latch_offline.py -> ../data/dl_dormancy_latch_offline_2010.txt
"""
import glob
import numpy as np
from netCDF4 import Dataset

R = "/Volumes/data02/LM4P/cases/phentest_2010/dayl_d/"
V = ("lai", "vegn_temp_max", "vegn_temp_min")
d = {k: [] for k in V}; lat = []; lon = []
for f in sorted(glob.glob(R + "*.land_daily.tile*.nc")):
    with Dataset(f) as A:
        A.set_auto_mask(False)
        lat.append(A["geolat_t"][:].ravel()); lon.append(A["geolon_t"][:].ravel())
        for k in V:
            x = A[k][:].astype("f8"); d[k].append(x.reshape(x.shape[0], -1))
lat = np.concatenate(lat); lon = np.concatenate(lon); lon = np.where(lon > 180, lon - 360, lon)
d = {k: np.concatenate(v, -1) for k, v in d.items()}
nt = d["lai"].shape[0]
ok = np.all((d["lai"] >= 0) & (d["lai"] < 1e10), 0) & np.all((d["vegn_temp_max"] > 100) & (d["vegn_temp_max"] < 400), 0)
ok &= (d["lai"].max(0) - d["lai"].min(0)) > 0.3
lat, lon = lat[ok], lon[ok]
tx, tn = d["vegn_temp_max"][:, ok] - 273.15, d["vegn_temp_min"][:, ok] - 273.15
tm = (tx + tn) / 2; gdd_inc = (np.maximum(tx, 0) + np.maximum(tn, 0)) / 2
nc_ = lat.size

doy = np.arange(1, nt + 1)[:, None]; rl = np.radians(lat)[None, :]
decl = np.radians(23.44) * np.sin(2 * np.pi * (284 + doy) / 365)
dayl = 24 / np.pi * np.arccos(np.clip(-np.tan(rl) * np.tan(decl), -1, 1))
shorten = (rl * np.cos(2 * np.pi * (284 + doy) / 365)) < 0
solst = np.where(lat >= 0, 355, 172)                    # local winter solstice (doy)
since_sol = (np.arange(1, nt + 1)[:, None] - solst[None, :]) % 365   # days after the local winter solstice


def release(name, t):
    if name in ("CUR", "HOLD12"):
        return np.ones(nc_, bool)
    if name.startswith("EQ"):
        return (~shorten[t]) & (dayl[t] >= float(name[2:]))
    return (since_sol[t] >= int(name[3:])) & (since_sol[t] < 182)   # only in the lengthening half-year after the solstice


def run(name):
    on = np.zeros(nc_, bool); latch = np.zeros(nc_, bool); gdd = np.zeros(nc_); tc = tm[:31].mean(0)
    events = np.zeros((nt, nc_), bool)
    for p in range(2):
        for t in range(nt):
            tc = 0.95 * tc + 0.05 * tm[t]
            if t == 0 and p == 0:
                gdd[:] = 0
            gdd += gdd_inc[t]
            latch &= ~release(name, t)
            turn_on = (~on) & (gdd > 180) & (tc >= 5) & (~latch)
            if name == "HOLD12":
                turn_on &= ~((dayl[t] < 12) & (tc < 20))
            turn_off = on & ((tc < 5) | (shorten[t] & (dayl[t] < 13) & (tc < 20)))
            on |= turn_on; on &= ~turn_off
            gdd[turn_off] = 0; latch |= turn_off
            if p == 1:
                events[t] = turn_on
    first_on = np.full(nc_, np.nan); winter = np.zeros(nc_, bool)
    for i in range(nc_):
        s = since_sol[:, i]; ev = np.where(events[:, i])[0]
        if ev.size:
            first_on[i] = s[ev].min(); winter[i] = (s[ev] < 60).any()
    return first_on, winter


# observed SOS 2010 (GIMMS, monthly -> daily, 50 % amplitude), expressed in days after the local winter solstice
g = Dataset("/Volumes/data01/MOF_LSM_project/poster/2026_LM4p_LAI/data/gimms_lai_mon_1982_2020.nc")
gv = [v for v in g.variables if g.variables[v].ndim == 3][0]
G = np.ma.filled(g[gv][(2010 - 1982) * 12:(2010 - 1982) * 12 + 12].astype("f8"), np.nan); G[np.abs(G) > 100] = np.nan
MID = np.array([15.5, 45, 74.5, 105, 135.5, 166, 196.5, 227.5, 258, 288.5, 319, 349.5]); D = np.arange(1, 366.0)
ii = np.clip(((lat + 90) // 1).astype(int), 0, 179); jj = np.clip(((lon + 180) // 1).astype(int), 0, 359)
obs = np.full(nc_, np.nan)
for i in range(nc_):
    m = G[:, ii[i], jj[i]]
    if not np.isfinite(m).all() or np.ptp(m) < 0.3:
        continue
    c = np.interp(D, np.r_[MID[-1] - 365, MID, MID[0] + 365], np.r_[m[-1], m, m[0]])
    c = np.roll(c, -int(solst[i]))                       # day 0 = local winter solstice
    thr = c.min() + 0.5 * np.ptp(c); ip = int(c.argmax())
    up = [k for k in range(ip) if c[k] < thr <= c[k + 1]]
    if up:
        obs[i] = up[-1]

BANDS = (("50-70N", 50, 70), ("40-50N", 40, 50), ("20-40N", 20, 40), ("20-40S", -40, -20), ("40-60S", -60, -40))
cands = ("CUR", "EQ12", "HOLD12", "EQ11", "SOL60", "SOL30")
res = {c: run(c) for c in cands}
out = ["Dormancy latch candidates, c3grass rules on dayl_d 2010 temperatures (offline state machine, drought ignored)",
       "per band: winter re-greening % (leaf-on < 60 d after local winter solstice) | median first leaf-on, days after solstice |"
       " obs SOS (GIMMS 2010) days after solstice; model LAI 50 % ~ leaf-on + 8 d", ""]
out.append("%-7s %5s | %-11s" % ("band", "cells", "obs SOS") + "".join(" | %-17s" % c for c in cands))
for nm, a, b in BANDS:
    m = (lat >= a) & (lat < b)
    row = "%-7s %5d | %6.0f     " % (nm, m.sum(), np.nanmedian(obs[m]))
    for c in cands:
        fo, w = res[c]
        row += " | %3.0f %% re, on %4.0f" % (100 * w[m].mean(), np.nanmedian(fo[m]))
    out.append(row)
open("../data/dl_dormancy_latch_offline_2010.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
