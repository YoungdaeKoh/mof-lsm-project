#!/usr/bin/env python
"""Check that CLM5 undid the accelerated-decomposition scaling when it left AD spinup.

The AD phase runs with spinup_state=2, which speeds up decomposition so the soil
pools reach equilibrium in ~200 years instead of ~10000.  The pools it equilibrates
are therefore far too small.  When the run continues with spinup_state=0, CLM reads
the AD restart, sees the mismatch, and multiplies the pools back up -- dead wood by
10 and each soil layer by its own accelerated factor.

If that rescaling silently failed, post-AD would start from a carbon-starved state
and the whole spinup would be wasted, so this compares the last AD year against the
first post-AD year and reports the jump.  The log message alone is not proof: it is
printed from the restart path whether or not the arithmetic landed.

Area-weighted with CLM's own `area` and `landfrac`, because an unweighted mean over
a regular lat/lon grid over-represents high latitudes -- see lsm-landmean-comparability.

Run on climate00:
  /home/ydkoh/anaconda3/bin/python verify_ad_exit_rescaling.py
"""

import numpy as np
from netCDF4 import Dataset

AD_LAST = ("/data2/ydkoh/cesm2_output/clm5_bgc_ad/run/"
           "clm5_bgc_ad.clm2.h0.0201-01-01-00000.nc")
PAD_FIRST = ("/data2/ydkoh/cesm2_output/clm5_bgc_pad/run/"
             "clm5_bgc_pad.clm2.h0.0001-01.nc")

# Pools the exit-spinup path touches, plus the totals they roll up into.
VARS = ["DEADSTEMC", "TOTSOMC", "TOTECOSYSC", "TOTVEGC", "TOTLITC", "CWDC"]


def land_mean(path, name):
    """Area-weighted mean over land, and the total in Pg C."""
    with Dataset(path) as ds:
        if name not in ds.variables:
            return None, None
        v = ds.variables[name][:]
        v = v[0] if v.ndim == 3 else v
        area = ds.variables["area"][:]          # km^2
        landfrac = ds.variables["landfrac"][:]

    v = np.ma.masked_invalid(np.ma.masked_greater(v, 1e35))
    w = np.ma.masked_array(area * landfrac, mask=v.mask)
    mean = float((v * w).sum() / w.sum())       # gC/m^2
    # gC/m^2 * km^2 -> Pg C:  *1e6 m^2/km^2 /1e15 g/Pg
    total = float((v * w).sum() * 1e6 / 1e15)
    return mean, total


print(f"{'variable':<12} {'AD last':>12} {'post-AD 1st':>12} {'ratio':>8}   "
      f"{'AD PgC':>9} {'pAD PgC':>9}")
print("-" * 70)
for name in VARS:
    a_mean, a_tot = land_mean(AD_LAST, name)
    p_mean, p_tot = land_mean(PAD_FIRST, name)
    if a_mean is None or p_mean is None:
        print(f"{name:<12} {'(absent)':>12}")
        continue
    ratio = p_mean / a_mean if a_mean else float("nan")
    print(f"{name:<12} {a_mean:12.1f} {p_mean:12.1f} {ratio:8.2f}   "
          f"{a_tot:9.1f} {p_tot:9.1f}")

print()
print("expected: DEADSTEMC ratio ~10 (the documented factor); TOTSOMC and CWDC")
print("well above 1 (layer-dependent factors); TOTVEGC close to 1 for the live")
print("pools, which AD does not scale.  A ratio of 1.00 for the soil pools means")
print("the rescaling did not happen and the post-AD run is starting carbon-starved.")
