#!/usr/bin/env python3
"""Offline sweep of the spring leaf-on gate: smoothing time scale tau (days) x gdd_crit, larix/c3grass thresholds.

Reconstructs the gate day per cell from the dayl_d 2010 daily output (spring rule identical to CTRL), as in
spring_gate_diag.py: leaf-on day = first day after doy 60 with GDD > gdd_crit AND T_tau >= 278.15 K AND theta >= 0.3,
  T_tau(d) = (1 - 1/tau) T_tau(d-1) + (1/tau) Tmean(d), Tmean = (Tmax+Tmin)/2 canopy temperature (vegn_temp_max/min),
  tau = 20 reproduces the code's tc_pheno (0.95/0.05). With the fixed patch (phenspring2) there is no spring leaf-off,
  so the first day all gates are open is the leaf-on day.
Target: shift of the gate day relative to CTRL (tau 20, gdd 180) should equal -(regional SOS bias, CTRL - GIMMS, 50 %
threshold, 2010; LM4 notes "봄 잎 나기 지연의 원인 진단"). Obs SOS spread between products ~6 d (p24) = tolerance.
Cells: 50-75N with LAI range > 0.3; AR6 regions; unweighted medians.
usage: python3 spring_sweep_offline.py <dayl_d dir> -> ../data/spring_sweep_offline_2010.txt
"""
import glob
import sys
import numpy as np
import regionmask
from netCDF4 import Dataset

run = sys.argv[1]
TAUS = (5, 7, 10, 15, 20)
GDDS = (100, 180, 250, 320, 360)
TC = 278.15
BIAS = {"NEU": 21, "NWN": 17, "NEN": 29, "WSB": 8, "ESB": 10, "RAR": 27, "RFE": 21}   # CTRL - GIMMS SOS, days

V = ("lai", "vegn_temp_max", "vegn_temp_min", "soil_liq", "soil_ice")
d = {k: [] for k in V}; lat = []; lon = []
for f in sorted(glob.glob(run + "/*.land_daily.tile*.nc")):
    with Dataset(f) as A:
        A.set_auto_mask(False)
        la = A.variables["geolat_t"][:].ravel(); lo = A.variables["geolon_t"][:].ravel()
        m = (la >= 50) & (la <= 75)
        lat.append(la[m]); lon.append(lo[m])
        for k in V:
            x = A.variables[k][:].astype("f8")
            x = x.reshape(x.shape[0], -1, m.size) if x.ndim == 3 else x.reshape(x.shape[0], m.size)
            d[k].append(x[..., m])
lat = np.concatenate(lat); lon = np.concatenate(lon); lon = np.where(lon > 180, lon - 360, lon)
d = {k: np.concatenate(v, axis=-1) for k, v in d.items()}
nt = d["lai"].shape[0]
lai = d["lai"]
ok = np.all((lai >= 0) & (lai < 1e10), 0) & np.all((d["vegn_temp_max"] > 100) & (d["vegn_temp_max"] < 400), 0) \
     & np.all(np.abs(d["soil_liq"]) < 1e10, (0, 1)) & ((lai.max(0) - lai.min(0)) > 0.3)
doy = np.arange(1, nt + 1)[:, None]
Tx, Tn = d["vegn_temp_max"], d["vegn_temp_min"]; tm = (Tx + Tn) / 2
gdd = np.cumsum((np.maximum(Tn - 273.16, 0) + np.maximum(Tx - 273.16, 0)) / 2, 0)
# soil-water gate (liquid only, top 10 cm, 30-day smoothing) as in spring_gate_diag.py
dz = np.array([0.02, 0.04, 0.04]); z = np.array([0.01, 0.04, 0.08]); wz = dz * np.exp(-z / 0.3); wz /= wz.sum()
liq = d["soil_liq"] / 1000.0; sat = np.maximum(((d["soil_liq"] + d["soil_ice"]) / 1000.0).max(0), 1e-3)
theta = (np.minimum(liq / sat, 1.0) * wz[None, :, None]).sum(1)
th = np.empty_like(theta); th[0] = theta[0]
for t in range(1, nt):
    th[t] = th[t - 1] + (theta[t] - th[t - 1]) / 31.0


def smooth(tau):
    s = np.empty_like(tm); s[0] = tm[:31].mean(0)
    for t in range(1, nt):
        s[t] = (1 - 1.0 / tau) * s[t - 1] + tm[t] / tau
    return s


def first(cond, start=60):
    c = cond & (doy > start)
    return np.where(c.any(0), np.argmax(c, 0) + 1, np.nan)


T = {tau: smooth(tau) for tau in TAUS}
wet = th >= 0.3
day = {}; bind = {}
for tau in TAUS:
    for g in GDDS:
        day[tau, g] = first((gdd > g) & (T[tau] >= TC) & wet)
        gates = np.vstack([first(gdd > g, 0), first(T[tau] >= TC), first(wet)])
        bind[tau, g] = np.nanargmax(np.where(np.isnan(gates), -1, gates), 0)   # 0 GDD, 1 T, 2 soil water

ar6 = regionmask.defined_regions.ar6.land
reg = np.array([ar6.mask(np.array([a]), np.array([b])).values.item() for a, b in zip(lon, lat)])
ref = day[20, 180]
lines = ["Offline spring gate sweep, dayl_d 2010, 50-75N cells with LAI range > 0.3, larix/c3grass tc_crit 278.15 K",
         "shift = median(gate day - CTRL gate day [tau 20, gdd 180]); target = -SOS bias (CTRL - GIMMS 2010, 50 %)",
         "err = shift - target (days, + = still late); bind% = share of cells where GDD / T_tau / soil water opens last"]
score = {}
for code, b in BIAS.items():
    m = ok & (reg == ar6.map_keys(code))
    lines.append("\n%s  cells %d  CTRL gate day %.0f  target shift %+d" % (code, m.sum(), np.nanmedian(ref[m]), -b))
    lines.append("  tau  gdd |  shift    err | bindGDD bindT bindW")
    for tau in TAUS:
        for g in GDDS:
            sh = np.nanmedian((day[tau, g] - ref)[m]); err = sh + b
            score.setdefault((tau, g), []).append(err)
            bb = bind[tau, g][m]
            lines.append("  %3d  %3d | %+6.0f %+6.0f | %6.0f %5.0f %5.0f" % (tau, g, sh, err, 100 * (bb == 0).mean(),
                                                                         100 * (bb == 1).mean(), 100 * (bb == 2).mean()))
lines.append("\nSummary over the 7 regions: RMS err (days) and max |err|; regions within the 6-day obs spread")
lines.append("  tau  gdd |   RMS  max|e| within6")
for (tau, g), e in sorted(score.items(), key=lambda kv: np.sqrt(np.mean(np.square(kv[1])))):
    e = np.array(e)
    lines.append("  %3d  %3d | %5.1f %6.1f %5d/7" % (tau, g, np.sqrt(np.mean(e ** 2)), np.abs(e).max(), (np.abs(e) <= 6).sum()))
open("../data/spring_sweep_offline_2010.txt", "w").write("\n".join(lines) + "\n")
i = lines.index("\nSummary over the 7 regions: RMS err (days) and max |err|; regions within the 6-day obs spread")
print("\n".join(lines[i:i + 10]))
