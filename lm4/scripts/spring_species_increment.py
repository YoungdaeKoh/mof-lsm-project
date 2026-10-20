#!/usr/bin/env python3
"""Which species makes the temperate early leaf-out under the 5-day spring gate? 2010, monthly LAI by species, C96.

Runs (same seed ctl y2009): base (CTRL), dayl_d (DL), daylspring5_full_d (DLS5), daylhold5_d (DLH5).
Per AR6 region / latitude band: land_area-weighted mean LAI of each species for Feb-May (all land cells in
the region, not the p26 GIMMS-amplitude subset), and the DLS5-DL / DLH5-DL increments.
Check: sum over species of by-species lai vs land_month lai (same weights).
output: ../data/spring_species_increment_2010.txt
"""
import glob
import shapely
import numpy as np
import regionmask
from netCDF4 import Dataset

R = "/Volumes/data02/LM4P/cases/phentest_2010/"
RUNS = [("CTRL", "base"), ("DL", "dayl_d"), ("DLS5", "daylspring5_full_d"), ("DLH5", "daylhold5_d")]
SPECIES = ["prioria", "picea", "larix", "acer", "c4grass", "c3grass"]
MONTHS = [1, 2, 3, 4]                          # Feb..May (0-based)
MNAME = ["Feb", "Mar", "Apr", "May"]
GROUPS = ["ENA", "EAS", "WCE", "40-50N", "30-40N", "NEU", "50-70N"]


def load(run):
    sp, tot, w, lat, lon = [], [], [], [], []
    for t in range(1, 7):
        f = R + run + "/20100101.land_month_by_species.tile%d.nc" % t
        with Dataset(f) as A:
            A.set_auto_mask(False)
            v = A["lai"][:].astype("f8")[:, :6]                 # (time, species, gi), drop "default"
        with Dataset(f.replace("land_month_by_species", "land_month")) as A:
            A.set_auto_mask(False)
            tl = A["lai"][:].astype("f8")
        with Dataset(f.replace("land_month_by_species", "land_static")) as A:
            A.set_auto_mask(False)
            a = A["land_area"][:].astype("f8").ravel()
        with Dataset(f.replace("land_month_by_species", "land_daily")) as A:
            A.set_auto_mask(False)
            la = A["geolat_t"][:].ravel(); lo = A["geolon_t"][:].ravel()
        assert v.shape[2] == tl.shape[1] == a.size == la.size
        sp.append(v); tot.append(tl); w.append(a); lat.append(la); lon.append(lo)
    sp = np.concatenate(sp, 2); tot = np.concatenate(tot, 1)
    sp[(sp < 0) | (sp > 1e10)] = 0.0
    tot[(tot < 0) | (tot > 1e10)] = np.nan
    return sp, tot, np.concatenate(w), np.concatenate(lat), np.concatenate(lon)


data = {name: load(run) for name, run in RUNS}
_, _, w, lat, lon = data["DL"]
for name in data:
    assert np.allclose(data[name][3], lat) and np.allclose(data[name][4], lon)
w = np.where(np.isfinite(w) & (w > 0) & (w < 1e15), w, 0.0)

ar6 = regionmask.defined_regions.ar6.land
lon180 = np.where(lon > 180, lon - 360, lon)
pts = shapely.points(lon180, lat)
masks = {}
for g in GROUPS:
    if g[0].isdigit():
        lo_, hi_ = [float(x) for x in g[:-1].split("-")]
        masks[g] = (lat >= lo_) & (lat < hi_)
    else:
        poly = ar6[[g]].polygons[0]
        masks[g] = shapely.contains(poly, pts)

out = ["Spring LAI by species, 2010, C96 land_area-weighted, all land cells in group",
       "check = sum of species lai vs land_month lai (DL, Feb-May), max abs diff of group means"]
for g in GROUPS:
    m = masks[g] & (w > 0)
    ww = w[m] / w[m].sum()
    sp_dl, tot_dl = data["DL"][0], data["DL"][1]
    chk = max(abs((sp_dl[k][:, m].sum(0) * ww).sum() - np.nansum(tot_dl[k][m] * ww)) for k in MONTHS)
    out.append("")
    out.append("%s  cells %d  check %.3f" % (g, m.sum(), chk))
    out.append("%-8s %-4s | " % ("species", "mon") + " ".join("%6s" % n for n, _ in RUNS) + " | DLS5-DL DLH5-DL")
    for s, sname in enumerate(SPECIES + ["total"]):
        for k, mn in zip(MONTHS, MNAME):
            vals = []
            for n, _ in RUNS:
                arr = data[n][0][k][:, m]
                v = arr.sum(0) if sname == "total" else arr[s]
                vals.append((v * ww).sum())
            if sname != "total" and max(vals) < 0.02:
                continue
            out.append("%-8s %-4s | " % (sname, mn) + " ".join("%6.2f" % v for v in vals)
                       + " | %+7.2f %+7.2f" % (vals[2] - vals[1], vals[3] - vals[1]))

open("../data/spring_species_increment_2010.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
