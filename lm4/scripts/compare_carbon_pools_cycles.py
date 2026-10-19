"""Fast vs slow carbon pools: LM4p spin-up cycle 1 (lm4_spinup30/archive_c1) vs cycle 2 (ctl 1981-2010).
Same mask and averaging as extract_monthly_noice.py (C96 points with lai defined = soil_area>0, minus Greenland
outline; unweighted mean over points, cubed sphere ~equal area) and the same Jan-Nov window as LM4 notes 13.62
(cycle 1 years 1981-1996 stop at November). Local copies of both archives.
Prints, per pool: 2010 value c1, c2, (c2-c1)/c1 %, and the 1981-2010 linear trend (% per 30 yr) in each cycle.
Output: lm4/data/carbon_pools_cycle1_vs_cycle2.csv (annual Jan-Nov means, both cycles)
"""
import numpy as np
from netCDF4 import Dataset
from greenland_mask import in_greenland

C1 = "/Volumes/data02/LM4P/cases/lm4_spinup30/archive_c1"
C2 = "/Volumes/data02/LM4P/cases/lm4p_ctl_1979-2024/archive"
OUT = "/Volumes/data01/MOF_LSM_project/lm4/data/carbon_pools_cycle1_vs_cycle2.csv"
YEARS = range(1981, 2011)
FILL = 1e30
POOLS = {"bl": "leaf", "br": "fine root", "nsc": "non-structural", "lflitt_C": "leaf litter",
         "fsc": "fast soil C", "bsw": "sapwood", "cwlitt_C": "coarse-wood litter", "ssc": "slow soil C",
         "tot_soil_C": "total soil C", "bwood": "wood", "lai": "LAI (ref)"}

MASK = {}
for t in range(1, 7):
    d = Dataset(f"{C2}/y2010/20100101.land_month.tile{t}.nc")
    a = np.ma.filled(d.variables["lai"][0].astype("f8"), np.nan); a[np.abs(a) > FILL] = np.nan
    MASK[t] = np.isfinite(a) & ~in_greenland(np.array(d.variables["geolat_t"][:]), np.array(d.variables["geolon_t"][:]))
    d.close()
print("non-ice land points:", sum(m.sum() for m in MASK.values()))

def annual(root):
    out = {k: [] for k in POOLS}
    for y in YEARS:
        s = {k: 0.0 for k in POOLS}; c = {k: 0.0 for k in POOLS}
        for t in range(1, 7):
            d = Dataset(f"{root}/y{y}/{y}0101.land_month.tile{t}.nc")
            for k in POOLS:
                a = np.ma.filled(d.variables[k][:11].astype("f8"), np.nan)   # Jan-Nov
                a[np.abs(a) > FILL] = np.nan
                a = np.where(MASK[t][None, :], a, np.nan)
                s[k] += np.nansum(a); c[k] += np.isfinite(a).sum()
            d.close()
        for k in POOLS:
            out[k].append(s[k] / c[k])
    return {k: np.array(v) for k, v in out.items()}

c1, c2 = annual(C1), annual(C2)
yrs = np.array(list(YEARS), "f8")
rows = [["pool", "cycle"] + [str(int(y)) for y in yrs]]
print(f"{'pool':12s} {'meaning':20s} {'c1 2010':>10s} {'c2 2010':>10s} {'c2-c1 %':>8s} | trend %/30yr c1 -> c2")
for k, lab in POOLS.items():
    tr = [100 * np.polyfit(yrs, v, 1)[0] * 30 / v.mean() for v in (c1[k], c2[k])]
    print(f"{k:12s} {lab:20s} {c1[k][-1]:10.4g} {c2[k][-1]:10.4g} {100*(c2[k][-1]-c1[k][-1])/c1[k][-1]:+8.2f} | "
          f"{tr[0]:+6.2f} -> {tr[1]:+6.2f}")
    rows += [[k, "c1"] + [f"{x:.6g}" for x in c1[k]], [k, "c2"] + [f"{x:.6g}" for x in c2[k]]]
np.savetxt(OUT, np.array(rows, dtype=object), fmt="%s", delimiter=",")
print("wrote", OUT)
