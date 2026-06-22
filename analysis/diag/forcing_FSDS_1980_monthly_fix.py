#!/usr/bin/env python3
"""ERA5->CLM transfer check FSDS 1980 after monthly-format fix.
Input ERA5 monthly FSDS vs CLM-received (model yr 0001 = 1980 monthly forcing)."""
import glob
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib import gridspec
import cartopy.crs as ccrs
from cartopy.util import add_cyclic_point

FD = "/Volumes/data01/MOF_LSM_project/data/forcing"
CLM_DIR = "/Volumes/data01/MOF_LSM_project/cesm/clm_output/I2000_ERA5_1980monthly"
g = xr.open_dataset(f"{FD}/era5_1979_annmean.nc")
ilat = g["LATIXY"].values[:, 0]; ilon = g["LONGXY"].values[0, :]

dc = xr.open_mfdataset(sorted(glob.glob(f"{CLM_DIR}/*.clm2.h0.0001-*.nc")),
                       combine="by_coords", use_cftime=True, decode_timedelta=False)
tc = dc["FSDS"].load()
tc = tc.assign_coords(month=("time", np.arange(1, 13))).swap_dims({"time": "month"})
clat = dc["lat"]; clon = dc["lon"]

fi = xr.open_dataset(f"{FD}/fsds_mon_1980.nc")
tin = xr.DataArray(fi["FSDS"].values, dims=("month", "lat", "lon"),
                   coords={"month": np.arange(1, 13), "lat": ilat, "lon": ilon})
tin_p = xr.concat([tin.isel(lon=-1).assign_coords(lon=ilon[-1]-360.), tin,
                   tin.isel(lon=0).assign_coords(lon=ilon[0]+360.)], dim="lon")
tin_r = tin_p.interp(lat=clat, lon=clon, method="linear")

landmask = ~np.isnan(tc.isel(month=0))
wlat = np.cos(np.deg2rad(clat))
tc_ts = tc.where(landmask).weighted(wlat).mean(("lat", "lon")).values
tin_ts = tin_r.where(landmask).weighted(wlat).mean(("lat", "lon")).values
rmse = np.sqrt(np.nanmean((tin_ts - tc_ts) ** 2))
tc_ann = tc.where(landmask).mean("month"); tin_ann = tin_r.where(landmask).mean("month")

fig = plt.figure(figsize=(13, 8))
gs = gridspec.GridSpec(2, 2, height_ratios=[1, 0.85], hspace=0.30, wspace=0.04)
def mp(pos, d, title):
    dd, lon = add_cyclic_point(np.asarray(d), coord=clon.values)
    ax = fig.add_subplot(pos, projection=ccrs.PlateCarree())
    im = ax.pcolormesh(lon, clat, dd, cmap="inferno", vmin=0, vmax=320,
                       shading="auto", transform=ccrs.PlateCarree())
    ax.coastlines(lw=0.5); ax.set_global()
    gl = ax.gridlines(draw_labels=True, lw=0.4, alpha=0.5, ls="--")
    gl.top_labels = False; gl.right_labels = False
    ax.set_title(title, fontsize=12); return ax, im
axa, im = mp(gs[0, 0], tin_ann, "(a) ERA5 forcing (input)")
axb, im = mp(gs[0, 1], tc_ann, "(b) CLM5 received (output)")
cb = fig.colorbar(im, ax=[axa, axb], orientation="horizontal", shrink=0.5,
                  aspect=40, pad=0.11, extend="max")
cb.set_label("Downward shortwave  FSDS (W/m²)")

sub = gs[1, :].subgridspec(1, 3, width_ratios=[1, 4, 1])
axc = fig.add_subplot(sub[0, 1])
mon = np.arange(1, 13)
axc.plot(mon, tin_ts, "-s", color="tab:blue", ms=7, label="ERA5 (input)")
axc.plot(mon, tc_ts, "--o", color="tab:red", ms=6, label="CLM5 (received)")
axc.set_xlabel("month"); axc.set_ylabel("land-mean FSDS (W/m²)")
axc.set_xticks(range(1, 13)); axc.grid(alpha=0.3); axc.legend()
axc.set_title(f"(c) Monthly FSDS — RMSE={rmse:.2f} W/m²  (monthly-format forcing, 1980)")
fig.suptitle("ERA5 forcing → CLM transfer check: FSDS 1980 (after monthly-format fix)",
             fontsize=13, y=0.98)
out = "/Volumes/data01/MOF_LSM_project/figures/forcing_FSDS_1980_monthly_fix.png"
fig.savefig(out, dpi=140, bbox_inches="tight")
print("saved:", out)
print(f"land-mean: input={np.nanmean(tin_ts):.2f}  CLM={np.nanmean(tc_ts):.2f}  RMSE={rmse:.3f}")
print("CLM monthly:", np.round(tc_ts, 1))
