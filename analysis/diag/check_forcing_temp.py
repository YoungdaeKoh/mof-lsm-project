#!/usr/bin/env python3
"""
Forcing-consistency check: CLM TSA (2m model temp) vs TBOT (forcing received).
Global-land area-mean monthly seasonal cycle, absolute (K and degC).
If TSA tracks TBOT closely -> ERA5 forcing correctly drives CLM.
"""
import glob
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

CLM_DIR = "/Volumes/data01/MOF_LSM_project/cesm/clm_output/I2000_ERA5_spinup/lnd/hist"
FIGDIR  = "/Volumes/data01/MOF_LSM_project/figures"

files = sorted(glob.glob(f"{CLM_DIR}/*.clm2.h0.*.nc"))
print(f"CLM files: {len(files)}")
ds = xr.open_mfdataset(files, combine="by_coords", use_cftime=True, decode_timedelta=False)
w = np.cos(np.deg2rad(ds["lat"]))

def land_seasonal(varname):
    am = ds[varname].weighted(w).mean(("lat", "lon"))     # land mean (NaN ocean skipped)
    return am.groupby("time.month").mean().values         # (12,) K

tsa  = land_seasonal("TSA")    # 2m model
tbot = land_seasonal("TBOT")   # forcing received
print("month  TBOT(K)  TSA(K)  TSA-TBOT")
for m in range(12):
    print(f"  {m+1:2d}   {tbot[m]:7.2f} {tsa[m]:7.2f}   {tsa[m]-tbot[m]:+.2f}")
print(f"mean |TSA-TBOT| = {np.nanmean(np.abs(tsa-tbot)):.3f} K")

mon = np.arange(1, 13)
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(mon, tbot-273.15, "-s", color="tab:blue", label="TBOT (ERA5 forcing → CLM)")
ax.plot(mon, tsa-273.15,  "-o", color="tab:red",  label="TSA (CLM 2m output)")
ax.set_xlabel("month"); ax.set_ylabel("temperature (°C)")
ax.set_title("Global-land 2m temperature: CLM output (TSA) vs ERA5 forcing (TBOT)\n"
             "1979-1987 monthly climatology")
ax.grid(alpha=0.3); ax.legend()
fig.tight_layout()
out = f"{FIGDIR}/forcing_temp_check.png"
fig.savefig(out, dpi=130)
print("saved:", out)
