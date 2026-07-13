#!/usr/bin/env python
# Noah-MP cyc2 (spun-up seed, 30 yr) in the CLM SpinupStability_SP 6-variable format.
# LDASOUT is ANNUAL INSTANTANEOUS output stamped Jan-01 00:00 -> HFX/LH/GPP are a single
# winter-midnight sample (GPP likely ~0 at night). State vars (soil M/T, TWS) are robust.
# Layers: soil water = layer 3 (node 0.70 m), soil temp = layer 4 (node 1.50 m); nearest to
# CLM's 0.80 m / 1.36 m. TWS = sum(SMC_i*dz_i)*1000 + SNEQV + WA [mm]. cos(lat) weighted.
import glob, os, re
import numpy as np
from netCDF4 import Dataset

A = "/home/ydkoh/HRLDAS/spinup_raw/noahmp_GSWP3_1deg_staticveg_cyc2"
SETUP = "/home/ydkoh/HRLDAS/forcing_GSWP3_1deg/init/HRLDAS_setup_GSWP3_1deg_d01.nc"
DZ = np.array([0.10, 0.30, 0.60, 1.00])
ds = Dataset(SETUP); ds.set_auto_mask(False)
iv = ds.variables["IVGTYP"][0].astype(int); xlat = ds.variables["XLAT"][0].astype("f8"); ds.close()
noice = (iv != 17) & (iv != 15)
wgt = np.cos(np.deg2rad(xlat))
def wm(a):
    a = np.asarray(a, "f8"); m = noice & np.isfinite(a) & (np.abs(a) < 1e10)
    return float(np.average(a[m], weights=wgt[m]))

files = sorted(glob.glob(f"{A}/*.LDASOUT_DOMAIN1"))
print("year,SM_L3,ST_L4,TWS,SWE")
for i, f in enumerate(files, 1):
    yr = int(re.search(r"(\d{4})\d{6}\.LDASOUT", os.path.basename(f)).group(1))
    d = Dataset(f); d.set_auto_mask(False)
    hfx = d.variables["HFX"][0]; lh = d.variables["LH"][0]; gpp = d.variables["GPP"][0]
    sm = d.variables["SOIL_M"][0]; st = d.variables["SOIL_T"][0]
    sn = d.variables["SNEQV"][0]; wa = d.variables["WA"][0]
    d.close()
    colw = 1000.0 * (sm * DZ[None, :, None]).sum(axis=1)   # layer axis=1 -> (sn,we)
    tws = colw + sn + wa
    print("%d,%.6f,%.4f,%.3f,%.4f" % (
        yr, wm(sm[:, 2, :]), wm(st[:, 3, :]), wm(tws), wm(sn)))
