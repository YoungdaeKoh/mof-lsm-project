#!/usr/bin/env python3
"""
Total freshwater discharge to ocean from MOSART (CLM river routing).
Global sum of TOTAL_DISCHARGE_TO_OCEAN_LIQ -> km3/yr, vs observed ~37-40k.
"""
import glob
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

ROF_DIR = "/Volumes/data01/MOF_LSM_project/cesm/clm_output/I2000_ERA5_spinup/rof/hist"
FIGDIR  = "/Volumes/data01/MOF_LSM_project/figures"

files = sorted(glob.glob(f"{ROF_DIR}/*.mosart.h0.*.nc"))
print(f"MOSART files: {len(files)}")
ds = xr.open_mfdataset(files, combine="by_coords", use_cftime=True, decode_timedelta=False)

# m3/s, per gridcell -> global sum = total flux to ocean
q = ds["TOTAL_DISCHARGE_TO_OCEAN_LIQ"]          # (time, lat, lon) m3/s
glob_m3s = q.sum(("lat", "lon"))                 # (time,) m3/s, monthly
# m3/s -> km3/yr : * seconds/yr / 1e9
SEC_YR = 365.0 * 86400.0
glob_km3yr = glob_m3s * SEC_YR / 1e9

vals = glob_km3yr.values
months = np.arange(len(vals))
print(f"global discharge: mean={np.nanmean(vals):.0f} km3/yr  "
      f"min={np.nanmin(vals):.0f} max={np.nanmax(vals):.0f}")

# annual means (model years)
nyr = len(vals) // 12
ann = np.nanmean(vals[:nyr*12].reshape(nyr, 12), axis=1)
print("annual (km3/yr):", np.round(ann).astype(int))

# plot: monthly series + annual + observed band
fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(months, vals, color="tab:blue", lw=0.8, alpha=0.6, label="monthly")
yr_mid = np.arange(nyr) * 12 + 6
ax.plot(yr_mid, ann, "-o", color="navy", label="annual mean")
ax.axhspan(37000, 40000, color="green", alpha=0.15,
           label="observed ~37-40k (Dai & Trenberth)")
ax.set_xlabel("model month (0001-01 = 1979)")
ax.set_ylabel("freshwater to ocean (km$^3$/yr)")
ax.set_title("CLM5+MOSART total discharge to ocean (1979-1986)")
ax.grid(alpha=0.3)
ax.legend()
fig.tight_layout()
out = f"{FIGDIR}/mosart_ocean_discharge.png"
fig.savefig(out, dpi=130)
print("saved:", out)
