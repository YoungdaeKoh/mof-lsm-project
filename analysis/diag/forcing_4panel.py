#!/usr/bin/env python3
"""
4-panel forcing transfer check:
  INPUT ERA5 forcing (0.5°, land-masked) vs CLM-received (h0, f19) — same vars.
Variables: TBOT, FSDS, FLDS, precip. Global-land monthly seasonal cycle.
Both lines overlapping => datm faithfully transfers forcing to CLM.
"""
import glob
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

CLM_DIR = "/Volumes/data01/MOF_LSM_project/cesm/clm_output/I2000_ERA5_spinup/lnd/hist"
INPUT_NC = "/Volumes/data01/MOF_LSM_project/data/era5land/input_forcing_landmean.nc"
FIGDIR  = "/Volumes/data01/MOF_LSM_project/figures"

# --- CLM-received (h0) global-land seasonal cycle ---
files = sorted(glob.glob(f"{CLM_DIR}/*.clm2.h0.*.nc"))
ds = xr.open_mfdataset(files, combine="by_coords", use_cftime=True, decode_timedelta=False)
w = np.cos(np.deg2rad(ds["lat"]))
def clm_clim(var, scale=1.0):
    am = (ds[var]*scale).weighted(w).mean(("lat", "lon"))
    return am.groupby("time.month").mean().values
clm = {
    "TBOT": clm_clim("TBOT") - 273.15,
    "precip": (clm_clim("RAIN", 86400.) + clm_clim("SNOW", 86400.)),  # mm/day
    "FSDS": clm_clim("FSDS"),
    "FLDS": clm_clim("FLDS"),
}

# --- INPUT forcing (land-masked, from NCL) ---
fin = xr.open_dataset(INPUT_NC)
lm = fin["landmean"].values            # (var, year, month); vars TBOT,FSDS,FLDS,PRECTmms
inp = {
    "TBOT":   lm[0].mean(axis=0) - 273.15,
    "FSDS":   lm[1].mean(axis=0),
    "FLDS":   lm[2].mean(axis=0),
    "precip": lm[3].mean(axis=0) * 86400.,   # mm/s -> mm/day
}

mon = np.arange(1, 13)
panels = [("TBOT", "(a) 기온 Temperature", "°C"),
          ("precip", "(b) 강수 Precipitation", "mm/day"),
          ("FSDS", "(c) 하향 단파 Shortwave", "W/m²"),
          ("FLDS", "(d) 하향 장파 Longwave", "W/m²")]
plt.rcParams["axes.unicode_minus"] = False
fig, axs = plt.subplots(2, 2, figsize=(12, 8.5))
for ax, (key, title, unit) in zip(axs.ravel(), panels):
    ax.plot(mon, inp[key], "-s", color="tab:blue", ms=7, label="ERA5 forcing (input, 0.5°)")
    ax.plot(mon, clm[key], "--o", color="tab:red", ms=5, label="CLM received (h0, f19)")
    ax.set_title(title); ax.set_ylabel(unit); ax.set_xlabel("month")
    ax.set_xticks(range(2, 13, 2)); ax.grid(alpha=0.3); ax.legend()
    rmse = np.sqrt(np.nanmean((inp[key]-clm[key])**2))
    ax.text(0.02, 0.04, f"RMSE={rmse:.3g}", transform=ax.transAxes, fontsize=9, color="grey")
fig.suptitle("Forcing transfer check: ERA5 input vs CLM-received (global-land, 1979-1987)\n"
             "두 선 겹침 = datm이 forcing을 CLM에 정상 전달", fontsize=12)
fig.tight_layout()
out = f"{FIGDIR}/forcing_transfer_4panel.png"
fig.savefig(out, dpi=140)
print("saved:", out)
for k in clm:
    print(f"{k}: input={np.nanmean(inp[k]):.2f}  CLM={np.nanmean(clm[k]):.2f}")
