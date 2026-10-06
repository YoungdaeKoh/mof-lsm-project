#!/usr/bin/env python3
"""How much do the water and energy fluxes respond when only the phenology rule changes?

Compares two phentest runs (same forcing, same initial state) over a latitude band on the
native C96 tiles: monthly means of LAI, transpiration, total evapotranspiration, soil
evaporation, sensible heat, runoff, canopy-air and 2 m temperature, GPP.
Weights: land area from land_static if present, else unweighted (C96 is quasi equal-area).
Note: evap_soil is NOT bare-soil evaporation. It exceeds evap_land in the output (1.31 vs
1.29 mm/d, 50-70N May 2010), so it is most likely the total vapour flux over the soil-covered
part of the cell; its definition was not checked in the source. Use transp and evap_land.
usage: python phentest_flux_response.py <ref_dir> <test_dir> [lat0 lat1]
"""
import glob
import os
import sys
import numpy as np
from netCDF4 import Dataset

a, b = sys.argv[1], sys.argv[2]
lat0, lat1 = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (50.0, 70.0)
VARS = [("lai", 1.0, "LAI m2/m2"), ("transp", 86400.0, "transpiration mm/d"), ("evap_land", 86400.0, "total ET mm/d"),
        ("evap_soil", 86400.0, "evap_soil (see note) mm/d"), ("sens", 1.0, "sensible heat W/m2"), ("runf", 86400.0, "runoff mm/d"),
        ("Tca", 1.0, "canopy-air T K"), ("t_ref", 1.0, "2 m T K"), ("gpp", 1.0, "GPP (file units)")]
acc = {v: [np.zeros(12), np.zeros(12), np.zeros(12)] for v, _, _ in VARS}   # sum ref, sum test, sum weight
for fa in sorted(glob.glob(a + "/*.land_month.tile*.nc")):
    fb = os.path.join(b, os.path.basename(fa))
    fs = fa.replace("land_month", "land_static")
    with Dataset(fa) as A, Dataset(fb) as B:
        A.set_auto_mask(False); B.set_auto_mask(False)
        lat = A.variables["geolat_t"][:].astype("f8").ravel()
        w0 = np.ones(lat.size)
        if os.path.exists(fs):
            with Dataset(fs) as S:
                S.set_auto_mask(False)
                for name in ("land_area", "area_land", "soil_area"):
                    if name in S.variables:
                        w0 = np.squeeze(S.variables[name][:]).astype("f8").ravel(); w0 = np.where(w0 > 0, w0, 0.0); break
        band = (lat >= lat0) & (lat < lat1)
        for v, _, _ in VARS:
            if v not in A.variables:
                continue
            x = A.variables[v][:12].astype("f8").reshape(12, -1); y = B.variables[v][:12].astype("f8").reshape(12, -1)
            fill = getattr(A.variables[v], "_FillValue", -1.0)
            for m in range(12):
                ok = band & (x[m] != fill) & (y[m] != fill) & np.isfinite(x[m]) & np.isfinite(y[m])
                acc[v][0][m] += (x[m][ok] * w0[ok]).sum(); acc[v][1][m] += (y[m][ok] * w0[ok]).sum(); acc[v][2][m] += w0[ok].sum()
print("band %g-%gN, ref = %s, test = %s" % (lat0, lat1, os.path.basename(a), os.path.basename(b)))
print("%-24s %s | Sep-Oct ref test change" % ("variable", " ".join("%7s" % m for m in ("May", "Jun", "Jul", "Aug", "Sep", "Oct"))))
for v, f, label in VARS:
    if acc[v][2].sum() == 0:
        continue
    r = acc[v][0] / acc[v][2] * f; t = acc[v][1] / acc[v][2] * f
    so_r, so_t = r[8:10].mean(), t[8:10].mean()
    chg = ("%+.2f K" % (so_t - so_r)) if v in ("Tca", "t_ref") else ("%+.1f %%" % ((so_t / so_r - 1) * 100))
    print("%-24s ref  %s | %8.3f" % (label, " ".join("%7.3f" % x for x in r[4:10]), so_r))
    print("%-24s test %s | %8.3f  %s" % ("", " ".join("%7.3f" % x for x in t[4:10]), so_t, chg))
