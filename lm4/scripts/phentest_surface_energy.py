#!/usr/bin/env python3
"""Does the earlier autumn leaf-off (DL13/12) change surface temperature and the energy balance? 2010, C96, monthly.

dayl_d (DL13/12) minus base (CTRL), same forcing (WFDE5 2010) and same 1 Jan 2010 state, so every difference comes from
the vegetation change. Fields: LAI, Trad (radiative surface temperature, ~ satellite LST), t_ref (2 m air, diagnosed by
the land model between the forcing level and the canopy air), soil_T top layer, sens (sensible heat), evap_land (ET),
albedo (direct beam, mean of the two bands), snow. Cells: 50-70N with CTRL LAI range > 0.3 (and all land 50-70N).
Plain means over C96 cells (quasi equal area). No obs here (offline: no atmospheric feedback).
output: ../data/phentest_surface_energy_2010.txt
"""
import glob
import numpy as np
from netCDF4 import Dataset

R = "/Volumes/data02/LM4P/cases/phentest_2010/"
V = ("lai", "Trad", "t_ref", "sens", "evap_land", "snow")


def load(run):
    d = {k: [] for k in V + ("soilT1", "alb")}; lat = []
    for f in sorted(glob.glob(R + run + "/20100101.land_month.tile*.nc")):
        with Dataset(f) as A:
            A.set_auto_mask(False)
            for k in V:
                d[k].append(A[k][:].astype("f8"))
            d["soilT1"].append(A["soil_T"][:, 0].astype("f8"))
            d["alb"].append(A["albedo_dir"][:].astype("f8").mean(1))
            lat.append(A["geolat_t"][:].ravel())
    d = {k: np.concatenate(v, -1) for k, v in d.items()}
    for k in d:
        d[k][np.abs(d[k]) > 1e10] = np.nan
    return d, np.concatenate(lat)


C, lat = load("base"); X, _ = load("dayl_d")
UNIT = {"lai": 1, "Trad": 1, "t_ref": 1, "soilT1": 1, "sens": 1, "evap_land": 86400.0, "alb": 1, "snow": 1}
NAME = {"lai": "LAI", "Trad": "Trad K", "t_ref": "t_ref K", "soilT1": "soilT1 K", "sens": "sens W/m2", "evap_land": "ET mm/d",
        "alb": "albedo", "snow": "snow kg/m2"}
veg = (np.nanmax(C["lai"], 0) - np.nanmin(C["lai"], 0)) > 0.3
out = ["DL13/12 - CTRL, 2010 monthly, C96 cell means (Jul .. Dec); CTRL value in brackets for Sep-Oct"]
for gname, m0 in (("50-70N, CTRL LAI range > 0.3", veg & (lat >= 50) & (lat < 70)), ("40-50N, CTRL LAI range > 0.3", veg & (lat >= 40) & (lat < 50))):
    out += ["", gname + "  (n %d)" % m0.sum(), "%-11s " % "" + " ".join("%7s" % s for s in ("Jul", "Aug", "Sep", "Oct", "Nov", "Dec")) + "   SepOct (CTRL)"]
    for k in ("lai", "alb", "Trad", "t_ref", "soilT1", "sens", "evap_land", "snow"):
        m = m0 & np.isfinite(C[k]).all(0) & np.isfinite(X[k]).all(0)
        dd = np.nanmean((X[k] - C[k])[:, m], 1) * UNIT[k]; cs = np.nanmean(C[k][8:10, m]) * UNIT[k]
        out.append("%-11s " % NAME[k] + " ".join("%+7.3f" % v for v in dd[6:12]) + "   %+7.3f (%.3f)" % (dd[8:10].mean(), cs))
open("../data/phentest_surface_energy_2010.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
