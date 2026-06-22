#!/usr/bin/env python3
"""
(1) 108-month time series of CLM TSA vs forcing TBOT (global land + East Asia)
(2) East-Asia regional seasonal cycle
Checks forcing->model fidelity beyond the global-mean cancellation.
"""
import glob
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

CLM_DIR = "/Volumes/data01/MOF_LSM_project/cesm/clm_output/I2000_ERA5_spinup/lnd/hist"
FIGDIR  = "/Volumes/data01/MOF_LSM_project/figures"

# East Asia box (covers Korea/China/Japan)
EA = dict(lat=slice(20, 50), lon=slice(100, 145))

files = sorted(glob.glob(f"{CLM_DIR}/*.clm2.h0.*.nc"))
print(f"CLM files: {len(files)}")
ds = xr.open_mfdataset(files, combine="by_coords", use_cftime=True, decode_timedelta=False)
nt = ds.sizes["time"]
mon_idx = np.arange(nt)

def land_mean(var, box=None):
    da = ds[var]
    if box:
        da = da.sel(**box)
        w = np.cos(np.deg2rad(da["lat"]))
    else:
        w = np.cos(np.deg2rad(ds["lat"]))
    return da.weighted(w).mean(("lat", "lon")).values   # (nt,)

tsa_g  = land_mean("TSA")  - 273.15
tbot_g = land_mean("TBOT") - 273.15
tsa_e  = land_mean("TSA",  EA) - 273.15
tbot_e = land_mean("TBOT", EA) - 273.15

# --- (1) 108-month time series ---
fig, axs = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
axs[0].plot(mon_idx, tbot_g, color="tab:blue", lw=1, label="TBOT (forcing)")
axs[0].plot(mon_idx, tsa_g,  color="tab:red",  lw=1, label="TSA (CLM)")
axs[0].set_title("Global land")
axs[1].plot(mon_idx, tbot_e, color="tab:blue", lw=1, label="TBOT (forcing)")
axs[1].plot(mon_idx, tsa_e,  color="tab:red",  lw=1, label="TSA (CLM)")
axs[1].set_title("East Asia (20-50N, 100-145E)")
for ax in axs:
    ax.set_ylabel("2m temp (°C)"); ax.grid(alpha=0.3); ax.legend(loc="upper right")
    for y in range(0, nt, 12):
        ax.axvline(y, color="grey", lw=0.3, alpha=0.5)
axs[1].set_xlabel("model month (0=1979-01 ... 107=1987-12)")
fig.suptitle("CLM TSA vs ERA5 forcing TBOT — 108-month time series")
fig.tight_layout()
fig.savefig(f"{FIGDIR}/temp_timeseries_108mon.png", dpi=130)

# --- (2) East Asia seasonal cycle (climatology) ---
def clim(x): return x.reshape(-1, 12).mean(axis=0)
mon = np.arange(1, 13)
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(mon, clim(tbot_e), "-s", color="tab:blue", label="TBOT (forcing)")
ax.plot(mon, clim(tsa_e),  "-o", color="tab:red",  label="TSA (CLM)")
ax.set_xlabel("month"); ax.set_ylabel("2m temp (°C)")
ax.set_title("East Asia 2m temperature seasonal cycle (1979-1987)\nCLM TSA vs ERA5 forcing TBOT")
ax.grid(alpha=0.3); ax.legend()
fig.tight_layout()
fig.savefig(f"{FIGDIR}/temp_seasonal_eastasia.png", dpi=130)

print(f"global  : amp TBOT={np.ptp(tbot_g.reshape(-1,12).mean(0)):.1f}  TSA={np.ptp(tsa_g.reshape(-1,12).mean(0)):.1f} °C")
print(f"EastAsia: amp TBOT={np.ptp(clim(tbot_e)):.1f}  TSA={np.ptp(clim(tsa_e)):.1f} °C, mean|TSA-TBOT|={np.mean(np.abs(tsa_e-tbot_e)):.2f}")
print("saved 2 figures")
