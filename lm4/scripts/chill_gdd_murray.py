#!/usr/bin/env python3
"""Murray et al. (1989) chilling-dependent forcing requirement on ERA5, converted to the LM4 GDD (0 degC base).

Murray, Cannell & Smith 1989 J. Appl. Ecol. 26:693, eqn (1) / Table 1:
  T_req = a + b exp(r C),  T = day-degrees > 5 degC since 1 January, C = days <= 5 degC since 1 November.
  Budburst = first day on which T >= T_req(C of that day).
Here daily mean ERA5 t2m replaces (max+min)/2 (assumption). For the predicted day we also report
  GDD0 = sum max(Tmean - 0 degC, 0) since 1 January, i.e. the LM4 gdd (gdd_base_T 273.16 K; LM4 uses (Tmax+Tmin) halves
  of canopy T and accumulates since the last cold leaf-off, approximated here from 1 January),
  and the day ERA5 GDD0 first exceeds 180 (larix/c3grass gdd_crit) for comparison.
Cells: 1-deg land (Natural Earth 110m) in the 7 boreal AR6 regions of spring_sweep_offline.py, 50-75N. Unweighted medians.
usage: python3 chill_gdd_murray.py [year] -> ../data/chill_gdd_murray_<year>.txt
"""
import sys
import numpy as np
import regionmask
from netCDF4 import Dataset

YR = int(sys.argv[1]) if len(sys.argv) > 1 else 2010
F = "/Volumes/data02/ERA5/ERA5_t2m_1deg_NH/ERA5davg_t2m_1deg_NH_%d.nc"
GROUPS = {"G2 spruce": (-56, 602, 0.991), "G3 birch": (36, 514, 0.981), "G4 larch": (39, 468, 0.974)}   # a, b, exp(r)
REGS = ("NEU", "NWN", "NEN", "WSB", "ESB", "RAR", "RFE")


def read(y):
    with Dataset(F % y) as A:
        A.set_auto_mask(False)
        return A["t2m"][:].astype("f8") - 273.15, A["latitude"][:], A["longitude"][:]


prev, lat, lon = read(YR - 1)
cur, lat2, lon2 = read(YR)
assert np.array_equal(lat, lat2) and np.array_equal(lon, lon2)
nov1 = 304 if prev.shape[0] == 365 else 305                      # 0-based index of 1 November
tt = np.concatenate([prev[nov1:], cur], 0)                       # 1 Nov (YR-1) .. 31 Dec YR
n0 = prev.shape[0] - nov1                                        # index of 1 January YR in tt
lo2d, la2d = np.meshgrid(np.where(lon > 180, lon - 360, lon), lat)
land = np.isfinite(regionmask.defined_regions.natural_earth_v5_0_0.land_110.mask(lo2d[0], la2d[:, 0]).values)
ar6 = regionmask.defined_regions.ar6.land
reg = ar6.mask(lo2d[0], la2d[:, 0]).values
sel = land & (la2d >= 50) & (la2d <= 75)

C = np.cumsum(tt <= 5.0, 0)                                      # chill days since 1 Nov
T5 = np.cumsum(np.where(np.arange(tt.shape[0])[:, None, None] >= n0, np.maximum(tt - 5.0, 0), 0), 0)
G0 = np.cumsum(np.where(np.arange(tt.shape[0])[:, None, None] >= n0, np.maximum(tt, 0), 0), 0)


def first(cond):
    return np.where(cond.any(0), np.argmax(cond, 0), -1)


out = {}
for g, (a, b, er) in GROUPS.items():
    req = a + b * np.exp(np.log(er) * C)
    k = first((T5 >= req) & (np.arange(tt.shape[0])[:, None, None] >= n0))
    ok = k >= 0
    kk = np.where(ok, k, 0)
    pick = lambda x: np.where(ok, np.take_along_axis(x, kk[None], 0)[0], np.nan)
    out[g] = dict(doy=np.where(ok, k - n0 + 1, np.nan), C=pick(C), req=pick(req), G0=pick(G0))
k180 = first(G0 > 180)
doy180 = np.where(k180 >= 0, k180 - n0 + 1, np.nan)

lines = ["Murray et al. 1989 chilling model on ERA5 daily mean t2m, budburst %d (chill from 1 Nov %d), 1-deg land 50-75N" % (YR, YR - 1),
         "doy = predicted budburst; C = chill days (<=5 C) at that day; req = T requirement (>5 C day-degrees);",
         "GDD0 = LM4-style GDD (>0 C, from 1 Jan) reached on that day; d180 = doy where ERA5 GDD0 > 180 (LM4 larix gdd_crit)"]
for code in REGS:
    m = sel & (reg == ar6.map_keys(code))
    lines.append("\n%s  cells %d  d180 %.0f" % (code, m.sum(), np.nanmedian(doy180[m])))
    lines.append("  %-10s | %5s %5s %5s %6s | %s" % ("group", "doy", "C", "req", "GDD0", "doy - d180"))
    for g, o in out.items():
        lines.append("  %-10s | %5.0f %5.0f %5.0f %6.0f | %+5.0f" % (g, np.nanmedian(o["doy"][m]), np.nanmedian(o["C"][m]),
                     np.nanmedian(o["req"][m]), np.nanmedian(o["G0"][m]), np.nanmedian((o["doy"] - doy180)[m])))
open("../data/chill_gdd_murray_%d.txt" % YR, "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
