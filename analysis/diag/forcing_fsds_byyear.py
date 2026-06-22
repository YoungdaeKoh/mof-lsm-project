#!/usr/bin/env python3
"""
ERA5 forcing -> CLM transfer check for FSDS, BY YEAR (1979-1987).
Input ERA5 monthly FSDS (0.5deg) regridded to CLM f19 grid, common CLM land mask.
3x3 panels: each year's land-mean monthly ERA5(input) vs CLM(received) + RMSE.
"""
import glob
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

FORCDIR = "/Volumes/data01/MOF_LSM_project/data/forcing"
CLM_DIR = "/Volumes/data01/MOF_LSM_project/cesm/clm_output/I2000_ERA5_spinup/lnd/hist"
FIGDIR  = "/Volumes/data01/MOF_LSM_project/figures"
YEARS   = list(range(1979, 1988))   # model yr 0001..0009
ANT     = -90.0

# 0.5deg input grid from the existing annmean file (LATIXY/LONGXY)
g = xr.open_dataset(f"{FORCDIR}/era5_1979_annmean.nc")
ilat = g["LATIXY"].values[:, 0]
ilon = g["LONGXY"].values[0, :]

results = []
for k, yr in enumerate(YEARS):
    mdlyr = k + 1
    # CLM received (f19), model year mdlyr
    cf = sorted(glob.glob(f"{CLM_DIR}/*.clm2.h0.{mdlyr:04d}-*.nc"))
    dc = xr.open_mfdataset(cf, combine="by_coords", use_cftime=True, decode_timedelta=False)
    tc = dc["FSDS"].load()
    tc = tc.assign_coords(month=("time", np.arange(1, 13))).swap_dims({"time": "month"})
    clat = dc["lat"]; clon = dc["lon"]

    # ERA5 input (0.5deg) -> CLM grid
    fi = xr.open_dataset(f"{FORCDIR}/fsds_mon_{yr}.nc")
    tin = xr.DataArray(fi["FSDS"].values, dims=("month", "lat", "lon"),
                       coords={"month": np.arange(1, 13), "lat": ilat, "lon": ilon})
    tin_p = xr.concat([tin.isel(lon=-1).assign_coords(lon=ilon[-1] - 360.),
                       tin,
                       tin.isel(lon=0).assign_coords(lon=ilon[0] + 360.)], dim="lon")
    tin_r = tin_p.interp(lat=clat, lon=clon, method="linear")

    landmask = (~np.isnan(tc.isel(month=0))) & (clat >= ANT)
    wlat = np.cos(np.deg2rad(clat))
    tc_ts  = tc.where(landmask).weighted(wlat).mean(("lat", "lon")).values
    tin_ts = tin_r.where(landmask).weighted(wlat).mean(("lat", "lon")).values
    rmse = np.sqrt(np.nanmean((tin_ts - tc_ts) ** 2))
    results.append((yr, tin_ts, tc_ts, rmse))
    print(f"{yr}: input={np.nanmean(tin_ts):.2f}  CLM={np.nanmean(tc_ts):.2f}  "
          f"bias(CLM-ERA5)={np.nanmean(tc_ts-tin_ts):+.2f}  RMSE={rmse:.2f} W/m2")

# --- 3x3 panels ---
fig, axs = plt.subplots(3, 3, figsize=(14, 11), sharex=True, sharey=True)
mon = np.arange(1, 13)
for ax, (yr, tin_ts, tc_ts, rmse) in zip(axs.flat, results):
    ax.plot(mon, tin_ts, "-s", color="tab:blue", ms=5, label="ERA5 (input)")
    ax.plot(mon, tc_ts, "--o", color="tab:red", ms=4, label="CLM5 (received)")
    ax.set_title(f"{yr}   RMSE={rmse:.2f} W/m²", fontsize=11)
    ax.grid(alpha=0.3); ax.set_xticks(range(1, 13, 2))
axs[0, 0].legend(fontsize=9, loc="upper left")
for ax in axs[:, 0]:
    ax.set_ylabel("land-mean FSDS (W/m²)")
for ax in axs[2, :]:
    ax.set_xlabel("month")
fig.suptitle("ERA5 forcing → CLM transfer check: FSDS by year (1979–1987)",
             fontsize=15, y=0.997)
fig.tight_layout(rect=[0, 0, 1, 0.98])
out = f"{FIGDIR}/forcing_FSDS_byyear.png"
fig.savefig(out, dpi=140, bbox_inches="tight")
print("saved:", out)

# annual RMSE / bias summary
print("\n=== annual summary ===")
for yr, tin_ts, tc_ts, rmse in results:
    print(f"  {yr}: RMSE={rmse:.2f}  mean-bias(CLM-ERA5)={np.nanmean(tc_ts-tin_ts):+.2f} W/m2")
