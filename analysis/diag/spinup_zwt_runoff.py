#!/usr/bin/env python3
"""
CLM5 spin-up convergence: water table depth (ZWT) & total runoff (QRUNOFF),
global-land monthly time series, 1979-1987 (108 months).
ZWT = slowest hydrology to equilibrate; QRUNOFF closes water budget (-> MOSART ocean).
"""
import glob
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

CLM_DIR = "/Volumes/data01/MOF_LSM_project/cesm/clm_output/I2000_ERA5_spinup/lnd/hist"
FIGDIR  = "/Volumes/data01/MOF_LSM_project/figures"

ds = xr.open_mfdataset(sorted(glob.glob(f"{CLM_DIR}/*.clm2.h0.*.nc")),
                       combine="by_coords", use_cftime=True, decode_timedelta=False)
nt = ds.sizes["time"]
w  = np.cos(np.deg2rad(ds["lat"]))
land = ~np.isnan(ds["H2OSOI"].isel(levsoi=0, time=0))

def lmean(var, scl=1.0):
    da = (ds[var]*scl).where(land)
    return da.weighted(w).mean(("lat","lon"), skipna=True).values

et    = lmean("QFLX_EVAP_TOT", 86400.)   # mm/day  (evapotranspiration)
qrun  = lmean("QRUNOFF", 86400.)         # mm/day  (total runoff)
mon   = np.arange(nt)

fig, axs = plt.subplots(2, 1, figsize=(8.7, 8), sharex=True)
axs[0].plot(mon, et, color="tab:green", lw=1.6)
axs[0].set_title("(a) CLM5 monthly evapotranspiration (ET, global-land)", fontsize=15)
axs[0].set_ylabel("ET (mm/day)", fontsize=15)
axs[1].plot(mon, qrun, color="tab:blue", lw=1.6)
axs[1].set_title("(b) CLM5 monthly total runoff (QRUNOFF, global-land)", fontsize=15)
axs[1].set_ylabel("runoff (mm/day)", fontsize=15)
for ax in axs:
    ax.grid(alpha=0.3); ax.tick_params(labelsize=13)
    for y in range(0, nt+1, 12): ax.axvline(y, color="grey", lw=0.3, alpha=0.5)
axs[1].set_xlabel("year", fontsize=15)
axs[1].set_xticks(range(0, nt+1, 12)); axs[1].set_xticklabels([f"{1979+i}" for i in range(10)])
fig.suptitle("CLM5 spin-up — evapotranspiration & runoff, monthly 1979-1987 (global land)", fontsize=15)
fig.tight_layout()
out = f"{FIGDIR}/spinup_et_runoff.png"
fig.savefig(out, dpi=140)
print("saved:", out)
print(f"ET      1979={et[:12].mean():.3f}  1987={et[-12:].mean():.3f} mm/day  (drift {et[-12:].mean()-et[:12].mean():+.3f})")
print(f"QRUNOFF 1979={qrun[:12].mean():.3f}  1987={qrun[-12:].mean():.3f} mm/day  (drift {qrun[-12:].mean()-qrun[:12].mean():+.3f})")
