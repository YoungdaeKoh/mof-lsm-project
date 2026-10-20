#!/usr/bin/env python3
"""(1) Soil temperature change by depth and (2) radiative surface temperature vs MODIS LST: CTRL (base) vs DL13/12 (dayl_d), 2010.

(1) soil_T (land_month, zfull_soil levels) dayl_d - base, monthly, cells 40-50N and 50-70N with CTRL LAI range > 0.3.
(2) Trad (monthly mean radiative surface temperature, all hours) vs MODIS MOD11C3.061 LST, (Day + Night)/2
    (overpasses ~10:30 / ~22:30 local, clear sky only; NH 0.05 deg NetCDF made by hdf2nc_mod11c3.py, grid checked
    2026-10-20: lat 0.025 -> 89.975 ascending, lon -179.975 .. 179.975, K, raw index plot = NH map, July Sahara day 50 /
    Greenland day -11 C). Obs averaged to 1 deg (20 x 20 pixels, >= 50 % valid) and taken at the 1-deg box holding each
    C96 centre (comparison on the model points). Caveat: (Day+Night)/2 of clear-sky LST is not a 24-h all-sky mean.
output: ../data/phentest_soilT_lst_2010.txt
"""
import glob
import numpy as np
from netCDF4 import Dataset

R = "/Volumes/data02/LM4P/cases/phentest_2010/"
M = "/Volumes/data02/MODIS/MOD11C3/nc/MOD11C3_LST_NH.2010%02d.nc"


def load(run):
    T, tr, lai, lat, lon = [], [], [], [], []
    for f in sorted(glob.glob(R + run + "/20100101.land_month.tile*.nc")):
        with Dataset(f) as A:
            A.set_auto_mask(False)
            T.append(A["soil_T"][:].astype("f8")); tr.append(A["Trad"][:].astype("f8")); lai.append(A["lai"][:].astype("f8"))
            lat.append(A["geolat_t"][:].ravel()); lon.append(A["geolon_t"][:].ravel()); z = A["zfull_soil"][:]
    out = [np.concatenate(v, -1) for v in (T, tr, lai)]
    for v in out:
        v[np.abs(v) > 1e10] = np.nan
    lon = np.concatenate(lon)
    return out, np.concatenate(lat), np.where(lon > 180, lon - 360, lon), z


(TC, trC, laiC), lat, lon, z = load("base")
(TX, trX, _), _, _, _ = load("dayl_d")
veg = (np.nanmax(laiC, 0) - np.nanmin(laiC, 0)) > 0.3
out = ["(1) soil_T dayl_d - base (K), 2010 monthly means over C96 cells; depth = zfull_soil (m)"]
for gname, g in (("50-70N", (lat >= 50) & (lat < 70)), ("40-50N", (lat >= 40) & (lat < 50))):
    m = veg & g & np.isfinite(TC).all((0, 1)) & np.isfinite(TX).all((0, 1))
    out += ["", "%s (n %d)  depth   " % (gname, m.sum()) + " ".join("%6s" % s for s in ("Jul", "Aug", "Sep", "Oct", "Nov", "Dec")) + "   min/max cell Oct"]
    for k in range(len(z)):
        if z[k] > 3.5:
            break
        d = (TX[:, k] - TC[:, k])[:, m]
        out.append("              %5.2f m " % z[k] + " ".join("%+6.3f" % v for v in d[6:12].mean(1)) + "   %+6.2f / %+6.2f" % (d[9].min(), d[9].max()))

# (2) LST
ci = np.clip(((lat + 90) // 1).astype(int), 0, 179); cj = np.clip(((lon + 180) // 1).astype(int), 0, 359)
lst = np.full((12, lat.size), np.nan)
for mo in range(12):
    with Dataset(M % (mo + 1)) as A:
        assert np.isclose(A["lat"][0], 0.025) and np.isclose(A["lon"][0], -179.975)
        x = 0.5 * (np.ma.filled(A["LST_Day"][:], np.nan) + np.ma.filled(A["LST_Night"][:], np.nan))
    b = x.reshape(90, 20, 360, 20)
    cnt = np.isfinite(b).sum((1, 3)); mean = np.nanmean(b, (1, 3)); mean[cnt < 200] = np.nan
    g1 = np.full((180, 360), np.nan); g1[90:] = mean
    lst[mo] = g1[ci, cj]
out += ["", "(2) Trad - MODIS LST (Day+Night)/2, K, 2010 monthly, C96 cells with CTRL LAI range > 0.3 and LST valid that month"]
for gname, g in (("50-70N", (lat >= 50) & (lat < 70)), ("40-50N", (lat >= 40) & (lat < 50))):
    out += ["", "%s   " % gname + " ".join("%6s" % s for s in "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())]
    for name, tr in (("CTRL", trC), ("DL13/12", trX)):
        row = []
        for mo in range(12):
            m = veg & g & np.isfinite(lst[mo]) & np.isfinite(tr[mo])
            row.append(np.mean(tr[mo, m] - lst[mo, m]) if m.sum() > 50 else np.nan)
        out.append("%-8s bias " % name + " ".join("%+6.2f" % v for v in row))
    nn = [(veg & g & np.isfinite(lst[mo])).sum() for mo in range(12)]
    out.append("cells        " + " ".join("%6d" % v for v in nn))
open("../data/phentest_soilT_lst_2010.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
