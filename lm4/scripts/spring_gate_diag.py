#!/usr/bin/env python3
"""Which leaf-on condition holds back spring in LM4+? (vegn_dynamics.F90 vegn_phenology_ppa, LEAF_OFF -> LEAF_ON)

Leaf-on needs all three: (1) GDD > gdd_crit  (2) tc_pheno >= tc_crit  (3) not drought: theta_av_phen >= cnst_crit_phen 0.3,
where theta = LIQUID water / vwc_sat (soil_tile.F90 soil_ave_theta1, frozen soil counts as dry) smoothed over 30 d
(vegetation.F90 tau_smooth_theta_phen). The run's daily output only allows a reconstruction:
  GDD   : sum from Jan 1 of (max(Tmin-273.16,0)+max(Tmax-273.16,0))/2 from vegn_temp_min/max (code resets at autumn
          leaf-off, so this misses post-leaf-off autumn days -> GDD day is an upper bound)
  tc    : tc_pheno(d) = 0.95 tc_pheno(d-1) + 0.05 Tmean(d), Tmean = (Tmax+Tmin)/2 canopy temperature, started at the
          January mean (the code uses canopy-air temperature, close to this offline)
  theta : top 3 soil layers only (0-10 cm, dz 0.02/0.04/0.04 m, weights dz*exp(-z/0.3)); vwc_sat taken as the annual max of
          (liq+ice)/1000 per layer; smoothed with weight 1/31 per day
Thresholds for the two deciduous types in 50-75N: larix/c3grass (gdd 180, tc 278.15 K) and acer (gdd 360, tc 283.16 K).
T5d = first day the raw 5-day mean canopy temperature reaches tc_crit (tc minus T5d = smoothing lag).
Model leaf-on = first day after doy 60 with LAI > min + 10 % of the annual range (cell-mean LAI, evergreen picea included).
For every cell the gate that opens LAST is the binding one; also prints snow-free day (snow_soil < 1 kg m-2 after the max).
usage: python3 spring_gate_diag.py <run_dir with daily lai>  -> ../data/spring_gate_diag_2010.txt
"""
import glob
import sys
import numpy as np
import regionmask
from netCDF4 import Dataset

run = sys.argv[1]
V = ("lai", "vegn_temp_max", "vegn_temp_min", "soil_liq", "soil_ice", "snow_soil")
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
lat = np.concatenate(lat); lon = np.where(np.concatenate(lon) > 180, np.concatenate(lon) - 360, np.concatenate(lon))
d = {k: np.concatenate(v, axis=-1) for k, v in d.items()}
nt = d["lai"].shape[0]
ok = np.all((d["lai"] >= 0) & (d["lai"] < 1e10), 0) & np.all((d["vegn_temp_max"] > 100) & (d["vegn_temp_max"] < 400), 0) \
     & np.all(np.abs(d["soil_liq"]) < 1e10, (0, 1)) & np.all(np.abs(d["snow_soil"]) < 1e10, 0)
lai = d["lai"]; rng = lai.max(0) - lai.min(0)
ok &= rng > 0.3                                   # cells with a real seasonal cycle
doy = np.arange(1, nt + 1)[:, None]


def first(cond, start=60):
    c = cond & (doy > start)
    return np.where(c.any(0), np.argmax(c, 0) + 1, 999)


on = first(lai > lai.min(0) + 0.1 * rng)
Tx, Tn = d["vegn_temp_max"], d["vegn_temp_min"]
gdd = np.cumsum((np.maximum(Tn - 273.16, 0) + np.maximum(Tx - 273.16, 0)) / 2, 0)
tm = (Tx + Tn) / 2; tc = np.empty_like(tm); tc[0] = tm[:31].mean(0)
for t in range(1, nt):
    tc[t] = 0.95 * tc[t - 1] + 0.05 * tm[t]
dz = np.array([0.02, 0.04, 0.04]); z = np.array([0.01, 0.04, 0.08]); wz = dz * np.exp(-z / 0.3); wz /= wz.sum()
liq = d["soil_liq"] / 1000.0; tot = (d["soil_liq"] + d["soil_ice"]) / 1000.0
sat = np.maximum(tot.max(0), 1e-3)
theta = (np.minimum(liq / sat, 1.0) * wz[None, :, None]).sum(1)
th = np.empty_like(theta); th[0] = theta[0]
for t in range(1, nt):
    th[t] = th[t - 1] + (theta[t] - th[t - 1]) / 31.0
smax = np.argmax(d["snow_soil"], 0)
snowfree = np.array([smax[i] + 1 + np.argmax(d["snow_soil"][smax[i]:, i] < 1.0) for i in range(lat.size)])

ar6 = regionmask.defined_regions.ar6.land
reg = np.array([ar6.mask(np.array([lo_]), np.array([la_])).values.item() for lo_, la_ in zip(lon, lat)])
lines = ["Spring leaf-on gates, %s, 2010, 50-75N cells with LAI range > 0.3 (unweighted; days of year)" % run.rstrip("/").split("/")[-1]]
for name, gc, tcc in (("larix/c3grass", 180, 278.15), ("acer", 360, 283.16)):
    g = {"GDD": first(gdd > gc, 0), "tc": first(tc >= tcc), "thaw": first(th >= 0.3)}
    traw = first(np.apply_along_axis(lambda a: np.convolve(a, np.ones(5) / 5, "same"), 0, tm) >= tcc)   # raw 5-day mean
    last = np.argmax(np.vstack([g["GDD"], g["tc"], g["thaw"]]), 0)
    lines.append("\nthresholds %s: gdd_crit %d, tc_crit %.2f K" % (name, gc, tcc))
    lines.append("%-6s %5s | %6s %6s %6s %6s %8s %6s | binding%%: %5s %5s %5s" % ("region", "cells", "GDD", "T5d", "tc", "thaw", "snowfree", "LAIon", "GDD", "tc", "thaw"))
    for code in ("all", "NEU", "RFE", "NWN", "ESB", "NEN", "WSB", "RAR"):
        m = ok.copy() if code == "all" else ok & (reg == ar6.map_keys(code))
        if m.sum() < 10:
            continue
        med = lambda a: np.median(a[m])
        lines.append("%-6s %5d | %6.0f %6.0f %6.0f %6.0f %8.0f %6.0f | %14.0f %5.0f %5.0f" % (
            code, m.sum(), med(g["GDD"]), med(traw), med(g["tc"]), med(g["thaw"]), med(snowfree), med(on),
            *[100 * np.mean(last[m] == k) for k in range(3)]))
open("../data/spring_gate_diag_2010.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
