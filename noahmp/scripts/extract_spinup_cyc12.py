#!/usr/bin/env python
# Extend extract_spinup_1deg.py over BOTH spin-up cycles and split ice / non-ice land.
#   deep T       = land-mean SOIL_T bottom layer (layer 4, ~1-2 m)
#   column water = land-mean 1000 * sum_i SMC_i * dz_i   [kg m-2], SMC = liquid+ice
# Ice-sheet columns (IGBP 15) never equilibrate offline, so they are reported separately.
# All means are cos(lat) AREA-WEIGHTED over the stated mask.
# Sampling: RESTART_FREQUENCY_HOURS=8760 is a fixed 365-day stride, so the restart date
# walks Jan-01 -> Dec-25 across a cycle. Same-date cycle-to-cycle differences are exact;
# the within-cycle series carries a <=7-day seasonal wobble. (LM4 samples Jan-01 fixed.)
# Emits CSV to stdout: cycle,spinyear,decyear,deepT_all,colw_all,deepT_noice,colw_noice,
#                      swe_noice,swe_ice,capped_ice,n_ice
import glob, os, re
import numpy as np
from netCDF4 import Dataset

DZ = np.array([0.10, 0.30, 0.60, 1.00])
SETUP = "/home/ydkoh/HRLDAS/forcing_GSWP3_1deg/init/HRLDAS_setup_GSWP3_1deg_d01.nc"
DIRS = [
    (1, "/home/ydkoh/HRLDAS/spinup_raw/noahmp_GSWP3_1deg_staticveg"),
    (2, "/home/ydkoh/HRLDAS/forcing_GSWP3_1deg/spinup"),
]
ICE, WATER = 15, 17

ds = Dataset(SETUP)
ds.set_auto_mask(False)
iv = ds.variables["IVGTYP"][0].astype(int)
xlat = ds.variables["XLAT"][0].astype("f8")
ds.close()

# cos(lat) area weight: a regular 1-deg lat/lon grid over-weights high latitudes if
# averaged unweighted. LM4 lives on a near-equal-area cubed sphere, so its unweighted
# land mean is already ~area-weighted -- weight here to make the two comparable.
wgt = np.cos(np.deg2rad(xlat))
land = iv != WATER
noice = land & (iv != ICE)
ice = land & (iv == ICE)


def amean(a, m):
    """cos(lat)-weighted mean of a over mask m."""
    return float(np.average(a[m], weights=wgt[m]))


def decyear(fn):
    m = re.search(r"RESTART\.(\d{4})(\d{2})(\d{2})", os.path.basename(fn))
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    doy = (np.datetime64(f"{y:04d}-{mo:02d}-{d:02d}") - np.datetime64(f"{y:04d}-01-01")).astype(int)
    return y + doy / 365.0


print("cycle,spinyear,decyear,deepT_all,colw_all,deepT_noice,colw_noice,swe_noice,swe_ice,capped_ice,n_ice")
seq = 0
for cyc, rdir in DIRS:
    files = [f for f in sorted(glob.glob(os.path.join(rdir, "RESTART.*_DOMAIN1"))) if "redated" not in f]
    for i, fn in enumerate(files):
        # cyc2's first restart is cyc1's last state re-dated; skip to avoid a duplicate point
        if cyc == 2 and i == 0:
            continue
        d = Dataset(fn)
        d.set_auto_mask(False)
        st = np.asarray(d["SOIL_T"][0], dtype="f8")
        sm = np.asarray(d["SMC"][0], dtype="f8")
        sn = np.asarray(d["SNEQV"][0], dtype="f8")
        d.close()
        deep = st[:, 3, :]
        colw = 1000.0 * (sm * DZ[None, :, None]).sum(axis=1)
        seq += 1
        # 6 decimals: the cycle-to-cycle drift in deep T is O(1e-6) K, and 4 decimals
        # rounds it to zero.
        print("%d,%d,%.4f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%d,%d" % (
            cyc, seq, decyear(fn),
            amean(deep, land), amean(colw, land),
            amean(deep, noice), amean(colw, noice), amean(sn, noice),
            amean(sn, ice), int((sn[ice] >= 4999.0).sum()), int(ice.sum())))
