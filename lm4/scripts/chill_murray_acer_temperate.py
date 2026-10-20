#!/usr/bin/env python3
"""Can a Murray et al. (1989) chilling-dependent forcing requirement brake the tau5 early leaf-out of LM4 acer in the
temperate zone while leaving the boreal gain alone? ERA5 daily mean t2m, 2010 (chill from 1 Nov 2009).

LM4 acer leaf-on gate emulated on t2m (acer has no field_table override -> code defaults tc_crit 283.16 K, gdd_crit 360):
  tcN  = exponential running mean of daily T with weight 1/N per day, started 1 Nov (N = 20 CTRL, 5 tau5)
  gate = first day from 1 Jan with tcN > 10 degC and GDD0 > 360 (GDD0 = sum max(T, 0) from 1 Jan)
  (LM4 uses canopy T and accumulates GDD since the last cold leaf-off; t2m and 1 Jan are approximations.)
Murray 1989 eqn (1): T_req = a + b exp(r C), T = day-degrees > 5 degC from 1 Jan, C = days <= 5 degC from 1 Nov.
  Acer is not among Murray's 15 species: bracket with Group 1 (Fagus, largest chilling need) and Group 3 (Betula,
  Corylus). 'excess' = b exp(r C) at budburst = requirement above the fully chilled floor a (0 -> saturated).
Combined rule = max(tau5 gate, Murray budburst): the delay it adds to the tau5 gate is compared with the delay
the DLS5 run needs (= minus its SOS bias, p26 table).
Cells: 1-deg land (Natural Earth 110m), AR6 regions and latitude bands. Unweighted medians (as chill_gdd_murray.py).
output: ../data/chill_murray_acer_temperate_2010.txt
"""
import numpy as np
import regionmask
from netCDF4 import Dataset

YR = 2010
F = "/Volumes/data02/ERA5/ERA5_t2m_1deg_NH/ERA5davg_t2m_1deg_NH_%d.nc"
GROUPS = {"G1 Fagus": (-147, 1084, 0.991), "G3 Betula": (36, 514, 0.981)}   # a, b, exp(r)
REGS = ("ENA", "EAS", "WCE", "40-50N", "30-40N", "NEU", "50-70N")
DLS5_SOS_BIAS = {"ENA": -23.3, "EAS": -59.2, "WCE": +3.6, "40-50N": -15.4, "NEU": +5.8, "50-70N": +7.9}   # p26, days


def read(y):
    with Dataset(F % y) as A:
        A.set_auto_mask(False)
        return A["t2m"][:].astype("f8") - 273.15, A["latitude"][:], A["longitude"][:]


prev, lat, lon = read(YR - 1)
cur, lat2, lon2 = read(YR)
assert np.array_equal(lat, lat2) and np.array_equal(lon, lon2)
nov1 = 304 if prev.shape[0] == 365 else 305
tt = np.concatenate([prev[nov1:], cur], 0)
n0 = prev.shape[0] - nov1
after = (np.arange(tt.shape[0]) >= n0)[:, None, None]
lo2d, la2d = np.meshgrid(np.where(lon > 180, lon - 360, lon), lat)
land = np.isfinite(regionmask.defined_regions.natural_earth_v5_0_0.land_110.mask(lo2d[0], la2d[:, 0]).values)
ar6 = regionmask.defined_regions.ar6.land
reg = ar6.mask(lo2d[0], la2d[:, 0]).values


def ema(x, n):
    out = np.empty_like(x); out[0] = x[0]
    for i in range(1, x.shape[0]):
        out[i] = out[i - 1] + (x[i] - out[i - 1]) / n
    return out


def first(cond):
    k = np.where(cond.any(0), np.argmax(cond, 0), -1)
    return np.where(k >= 0, k - n0 + 1, np.nan)


C = np.cumsum(tt <= 5.0, 0)
T5 = np.cumsum(np.where(after, np.maximum(tt - 5.0, 0), 0), 0)
G0 = np.cumsum(np.where(after, np.maximum(tt, 0), 0), 0)
gate = {n: first((ema(tt, n) > 10.0) & (G0 > 360) & after) for n in (20, 5)}
mur = {}
for g, (a, b, er) in GROUPS.items():
    req = a + b * np.exp(np.log(er) * C)
    k = (T5 >= req) & after
    d = first(k)
    kk = np.where(np.isfinite(d), d + n0 - 1, 0).astype(int)
    mur[g] = dict(doy=d, C=np.take_along_axis(C, kk[None], 0)[0].astype("f8"),
                  exc=np.take_along_axis(req - a, kk[None], 0)[0])

masks = {}
for r in REGS:
    if r[0].isdigit():
        lo_, hi_ = [float(x) for x in r[:-1].split("-")]
        masks[r] = land & (la2d >= lo_) & (la2d < hi_)
    else:
        masks[r] = land & (reg == ar6.map_keys(r))

L = ["Murray 1989 chilling vs LM4 acer gate on ERA5 t2m, budburst %d (chill from 1 Nov %d), 1-deg land, medians" % (YR, YR - 1),
     "g20/g5 = acer gate doy with 20-d / 5-d smoothed T (>10 C) and GDD0 > 360; Murray doy, C = chill days, exc = b exp(rC)",
     "delay = median over cells of max(g5, Murray) - g5; need = -(DLS5 SOS bias) from p26 (positive = must be later)"]
for r in REGS:
    m = masks[r] & np.isfinite(gate[5])
    L.append("\n%s  cells %d  g20 %.0f  g5 %.0f  (g5-g20 %+.0f)  need %s" % (
        r, m.sum(), np.nanmedian(gate[20][m]), np.nanmedian(gate[5][m]), np.nanmedian((gate[5] - gate[20])[m]),
        "%+.0f" % -DLS5_SOS_BIAS[r] if r in DLS5_SOS_BIAS else "-"))
    L.append("  %-10s | %5s %5s %6s | %6s %8s" % ("group", "doy", "C", "exc", "delay", "%delayed"))
    for g, o in mur.items():
        dl = np.fmax(o["doy"], gate[5]) - gate[5]
        L.append("  %-10s | %5.0f %5.0f %6.0f | %+6.0f %7.0f%%" % (
            g, np.nanmedian(o["doy"][m]), np.nanmedian(o["C"][m]), np.nanmedian(o["exc"][m]),
            np.nanmedian(dl[m]), 100 * np.mean(dl[m] > 0)))
open("../data/chill_murray_acer_temperate_%d.txt" % YR, "w").write("\n".join(L) + "\n")
print("\n".join(L))
