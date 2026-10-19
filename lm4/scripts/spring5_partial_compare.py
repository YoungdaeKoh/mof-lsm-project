#!/usr/bin/env python3
"""Spring leaf-on with the 5-day smoothed gate (daylspring5_d) vs the 20-day gate (dayl_d), same DL13/12 autumn, 2010.

daylspring5_d may still be running: its daily files are local copies whose numrecs was patched to the complete
records on disk, so only the first NT common days are used (cut at doy NT, enough for spring).
Leaf-on = first day after doy 60 with LAI > min + 10 % of the Jan..NT range (as spring_gate_diag.py).
Cells: 50-75N with dayl_d LAI range > 0.3. Regions: AR6 land. Unweighted medians (days) and means (LAI).
usage: python3 spring5_partial_compare.py <exp_dir> <ref_dir> -> ../data/spring5_partial_compare_2010.txt
"""
import glob
import sys
import numpy as np
import regionmask
from netCDF4 import Dataset

exp, ref = sys.argv[1], sys.argv[2]


def load(run, coord_run):
    # geolat_t/geolon_t are written only when a file is closed -> take them from the finished run (grid_index identical)
    lai, lat, lon = [], [], []
    for f, fc in zip(sorted(glob.glob(run + "/*.land_daily.tile*.nc")), sorted(glob.glob(coord_run + "/*.land_daily.tile*.nc"))):
        with Dataset(f) as A, Dataset(fc) as C:
            A.set_auto_mask(False); C.set_auto_mask(False)
            assert np.array_equal(A.variables["grid_index"][:], C.variables["grid_index"][:])
            la = C.variables["geolat_t"][:].ravel(); lo = C.variables["geolon_t"][:].ravel()
            m = (la >= 50) & (la <= 75)
            x = A.variables["lai"][:].astype("f8"); x = x.reshape(x.shape[0], m.size)[:, m]
            lai.append(x); lat.append(la[m]); lon.append(lo[m])
    nt = min(a.shape[0] for a in lai)
    lo = np.concatenate(lon)
    return np.concatenate([a[:nt] for a in lai], 1), np.concatenate(lat), np.where(lo > 180, lo - 360, lo)


le, lat, lon = load(exp, ref); lr, _, _ = load(ref, ref)
NT = min(le.shape[0], lr.shape[0]); le, lr = le[:NT], lr[:NT]
ok = np.all((lr >= 0) & (lr < 1e10), 0) & np.all((le >= 0) & (le < 1e10), 0)
ok &= (lr.max(0) - lr.min(0)) > 0.3
doy = np.arange(1, NT + 1)[:, None]


def leaf_on(lai):
    rng = lai.max(0) - lai.min(0); c = (lai > lai.min(0) + 0.1 * rng) & (doy > 60)
    return np.where(c.any(0), np.argmax(c, 0) + 1, np.nan)


on_e, on_r = leaf_on(le), leaf_on(lr)
ar6 = regionmask.defined_regions.ar6.land
reg = np.array([ar6.mask(np.array([a]), np.array([b])).values.item() for a, b in zip(lon, lat)])
lines = ["daylspring5_d (5-day spring gate) vs dayl_d (20-day), 2010 doy 1-%d, 50-75N cells with LAI range > 0.3" % NT,
         "%-5s %5s | %7s %7s %6s | %6s %6s %6s | %6s %6s %6s" % ("reg", "cells", "on_ref", "on_exp", "d_on",
                                                                   "May_r", "May_e", "dMay%", "Jun_r", "Jun_e", "dJun%")]
for code in ("all", "NEU", "RFE", "NWN", "ESB", "NEN", "WSB", "RAR"):
    m = ok.copy() if code == "all" else ok & (reg == ar6.map_keys(code))
    if m.sum() < 10:
        continue
    may = slice(120, 151); jun = slice(151, 181)
    mr, me = lr[may][:, m].mean(), le[may][:, m].mean(); jr, je = lr[jun][:, m].mean(), le[jun][:, m].mean()
    lines.append("%-5s %5d | %7.0f %7.0f %+6.0f | %6.2f %6.2f %+6.0f | %6.2f %6.2f %+6.0f" % (
        code, m.sum(), np.nanmedian(on_r[m]), np.nanmedian(on_e[m]), np.nanmedian((on_e - on_r)[m]),
        mr, me, 100 * (me - mr) / mr, jr, je, 100 * (je - jr) / jr))
open("../data/spring5_partial_compare_2010.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
