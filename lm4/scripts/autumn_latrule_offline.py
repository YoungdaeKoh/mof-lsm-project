#!/usr/bin/env python3
"""Offline prediction of the autumn leaf-off day for a latitude-dependent day-length threshold x temperature gate.

Rule in the code (lm4P.phenology_autumn_daylength.diff), leaf-off on the first day with
    tc_pheno < tc_crit (cold rule, 278.15 K)  OR  (shortening AND dayl < dayl_crit_off AND tc_pheno < tc_crit_off).
Reconstructed per C96 cell from the dayl_d 2010 daily output: tc_pheno = 20-day EMA (0.95/0.05) of the 2 m air
temperature (t_ref_max + t_ref_min)/2 as a proxy for canopy temperature, day length from Cooper + sunrise equation (as the patch).
Variants: OLD = 13 h (larix, c3grass) / 12 h (acer) by the CTRL July dominant species, tc_crit_off 20 C (= dayl_d);
          LAT = 12.0 + 0.05 (|lat| - 40) h for all three species, tc_crit_off 20 / 15 / 12 / 10 C.
Predicted 50 % EOS = trigger day + the cell's own lag (dayl_d EOS50 - OLD trigger), i.e. the decline after the switch
is assumed unchanged. Obs EOS = mean of GIMMS-cons / AVHRR / GLASS 2010 (p25 method, 1 deg, GIMMS amplitude >= 0.5)
at the 1-deg box holding the C96 centre. Also tc_pheno on the observed EOS day (maritime vs continental).
Cells: NH 25-75N, rule species (larix + acer + c3grass) >= 50 % of CTRL July leaf area, dayl_d LAI range > 0.3.
output: ../data/autumn_latrule_offline_2010.txt
"""
import glob
import shapely
import numpy as np
import netCDF4 as nc
import regionmask

R = "/Volumes/data02/LM4P/cases/phentest_2010/dayl_d/"
P = "/Volumes/data01/MOF_LSM_project/poster/2026_LM4p_LAI/data/"
DOY = np.arange(1, 366)
TC = 278.15
TOFF = (20, 15, 12, 10)

# ---- model daily
V = ("lai", "t_ref_max", "t_ref_min")   # vegn_temp_max/min are corrupt in many cells (WCE Sep min -166 C), 2 m air used
d = {k: [] for k in V}; lat = []; lon = []
for f in sorted(glob.glob(R + "20100101.land_daily.tile*.nc")):
    with nc.Dataset(f) as A:
        A.set_auto_mask(False)
        for k in V:
            d[k].append(A[k][:].astype("f8").reshape(365, -1))
        lat.append(A["geolat_t"][:].ravel()); lon.append(A["geolon_t"][:].ravel())
d = {k: np.concatenate(v, 1) for k, v in d.items()}
lat = np.concatenate(lat); lon = np.concatenate(lon); lon = np.where(lon > 180, lon - 360, lon)
z = np.load(P + "base_species_share_july2010_c96.npz", allow_pickle=True)
assert np.allclose(z["lat"], lat) and np.allclose(np.where(z["lon"] > 180, z["lon"] - 360, z["lon"]), lon)
sp = list(z["species"]); sh = z["share"]
rule = sh[sp.index("larix")] + sh[sp.index("acer")] + sh[sp.index("c3grass")]
acer_dom = sh[sp.index("acer")] > sh[sp.index("larix")] + sh[sp.index("c3grass")]

lai = d["lai"]; tm = (d["t_ref_max"] + d["t_ref_min"]) / 2
ok = np.all((lai >= 0) & (lai < 1e10), 0) & np.all((tm > 150) & (tm < 400), 0) & ((lai.max(0) - lai.min(0)) > 0.3) \
     & (lat >= 25) & (lat < 75) & (rule >= 0.5)
tc = np.empty_like(tm); tc[0] = tm[0]
for t in range(1, 365):
    tc[t] = 0.95 * tc[t - 1] + 0.05 * tm[t]

decl = np.radians(23.44) * np.sin(2 * np.pi * (284 + DOY) / 365)
dayl = 24 / np.pi * np.arccos(np.clip(-np.tan(np.radians(lat))[None, :] * np.tan(decl)[:, None], -1, 1))
short = (np.radians(lat)[None, :] * np.cos(2 * np.pi * (284 + DOY) / 365)[:, None]) < 0


def trigger(crit, toff):
    c = (tc < TC) | (short & (dayl < crit[None, :]) & (tc < toff + 273.15))
    c[:182] = False                                   # autumn only (after the June solstice)
    return np.where(c.any(0), c.argmax(0) + 1.0, np.nan)


old_crit = np.where(acer_dom, 12.0, 13.0)
lat_crit = 12.0 + 0.05 * (np.abs(lat) - 40)
trig = {"OLD 13/12, 20C": trigger(old_crit, 20)}
for t in TOFF:
    trig["LAT, %dC" % t] = trigger(lat_crit, t)

# model 50 % EOS (daily) and lag after the OLD trigger
amp_lo, amp_hi = lai.min(0), lai.max(0); ip = lai.argmax(0)
thr = amp_lo + 0.5 * (amp_hi - amp_lo)
below = (lai < thr[None, :]) & (DOY[:, None] > ip[None, :] + 1)
eos_mod = np.where(below.any(0), below.argmax(0) + 1.0, np.nan)
lag = eos_mod - trig["OLD 13/12, 20C"]
print("sanity: cells %d, OLD trigger after the model 50 %% EOS (lag < 0) in %.1f %%, lag > 60 d in %.1f %%" % (
    ok.sum(), 100 * np.mean(lag[ok] < 0), 100 * np.mean(lag[ok] > 60)))

# ---- obs EOS 2010, 1 deg (p25 method)
MID = np.array([15.5, 45, 74.5, 105, 135.5, 166, 196.5, 227.5, 258, 288.5, 319, 349.5])
obs = []
for f, y0 in (("gimms_lai_mon_1982_2020.nc", 1982), ("gimms_solely_lai_mon_1982_2015.nc", 1982), ("glass_lai_modis_monthly_1deg_2001_2020.nc", 2001)):
    with nc.Dataset(P + f) as A:
        assert np.isclose(A["lat"][0], -89.5) and np.isclose(A["lon"][0], -179.5)
        x = np.ma.filled(A["lai"][(2010 - y0) * 12:(2010 - y0) * 12 + 12].astype("f8"), np.nan)
    x[np.abs(x) > 100] = np.nan; obs.append(x)
gamp = np.nanmax(obs[0], 0) - np.nanmin(obs[0], 0)
ci = np.clip(((lat + 90) // 1).astype(int), 0, 179); cj = np.clip(((lon + 180) // 1).astype(int), 0, 359)
eos_obs = np.full(lat.size, np.nan)
for n in np.where(ok & (gamp[ci, cj] >= 0.5))[0]:
    es = []
    for x in obs:
        m = x[:, ci[n], cj[n]]
        if not np.isfinite(m).all():
            break
        c = np.interp(DOY, np.r_[MID[-1] - 365, MID, MID[0] + 365], np.r_[m[-1], m, m[0]])
        th = c.min() + 0.5 * (c.max() - c.min()); k0 = int(c.argmax())
        dn = [k for k in range(k0, 364) if c[k] >= th > c[k + 1]]
        if not dn:
            break
        k = dn[0]; es.append(DOY[k] + (c[k] - th) / (c[k] - c[k + 1]))
    if len(es) == 3:
        eos_obs[n] = np.mean(es)
tc_obs = np.full(lat.size, np.nan); v = np.isfinite(eos_obs)
tc_obs[v] = tc[np.round(eos_obs[v]).astype(int) - 1, np.where(v)[0]] - 273.15

# ---- regional summary
ar6 = regionmask.defined_regions.ar6.land
GROUPS = [("50-70N", (lat >= 50) & (lat < 70))] + [(c, shapely.contains_xy(ar6[c].polygon, lon, lat)) for c in
          ("NEU", "NEN", "ENA", "WCE", "EEU", "WSB", "ESB", "NWN", "RFE", "RAR", "EAS", "TIB")]
keys = list(trig)
out = ["Offline autumn rule, dayl_d 2010; predicted EOS bias = trigger + own lag - obs EOS (days, median over cells)",
       "check: dayl_d actual EOS bias in the same cells = column 'dayl_d'; tc_obs = tc_pheno (C) on the observed EOS day",
       "%-7s %5s %6s %6s %6s | %7s | " % ("region", "cells", "lag", "EOSobs", "tc_obs", "dayl_d") + " ".join("%13s" % k for k in keys)]
for name, sel in GROUPS:
    m = ok & sel & np.isfinite(eos_obs) & np.isfinite(lag)
    if m.sum() < 10:
        continue
    row = [np.nanmedian((trig[k] + lag - eos_obs)[m]) for k in keys]
    out.append("%-7s %5d %6.1f %6.0f %6.1f | %+7.1f | " % (name, m.sum(), np.median(lag[m]), np.median(eos_obs[m]), np.median(tc_obs[m]),
               np.median((eos_mod - eos_obs)[m])) + " ".join("%+13.1f" % x for x in row))
open("../data/autumn_latrule_offline_2010.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
