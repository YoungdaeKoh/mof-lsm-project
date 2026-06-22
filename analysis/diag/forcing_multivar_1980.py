#!/usr/bin/env python3
"""ERA5->CLM transfer check (1980, monthly-format) for multiple variables.
Input allmon_1980.nc vs CLM-received (model yr 0001). Maps + monthly land-mean."""
import glob
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib import gridspec
import cartopy.crs as ccrs
from cartopy.util import add_cyclic_point

FD = "/Volumes/data01/MOF_LSM_project/data/forcing"
CLM_DIR = "/Volumes/data01/MOF_LSM_project/cesm/clm_output/I2000_ERA5_1980monthly"
FIG = "/Volumes/data01/MOF_LSM_project/figures"

g = xr.open_dataset(f"{FD}/era5_1979_annmean.nc")
ilat = g["LATIXY"].values[:, 0]; ilon = g["LONGXY"].values[0, :]

CFG = {
 "TBOT":  dict(invar="TBOT",     off=-273.15, scl=1.,    clm=["TBOT"],        clmoff=-273.15, clmscl=1.,
               cmap="RdYlBu_r", vmin=-35, vmax=35, ext="both", unit="°C",     long="2m air temperature  TBOT"),
 "PRECT": dict(invar="PRECTmms", off=0.,      scl=86400.,clm=["RAIN","SNOW"], clmoff=0.,     clmscl=86400.,
               cmap="YlGnBu",   vmin=0,   vmax=10, ext="max",  unit="mm/day", long="Precipitation  RAIN+SNOW"),
 "FLDS":  dict(invar="FLDS",     off=0.,      scl=1.,    clm=["FLDS"],        clmoff=0.,     clmscl=1.,
               cmap="magma",    vmin=150, vmax=450,ext="both", unit="W/m²",   long="Downward longwave  FLDS"),
}

dc = xr.open_mfdataset(sorted(glob.glob(f"{CLM_DIR}/*.clm2.h0.0001-*.nc")),
                       combine="by_coords", use_cftime=True, decode_timedelta=False)
clat = dc["lat"]; clon = dc["lon"]

def doplot(VAR):
    c = CFG[VAR]
    fin = xr.open_dataset(f"{FD}/{c['invar']}_mon_1980.nc")
    tc_raw = sum(dc[v] for v in c["clm"])
    tc = (tc_raw * c["clmscl"] + c["clmoff"]).load()
    tc = tc.assign_coords(month=("time", np.arange(1, 13))).swap_dims({"time": "month"})
    tin = xr.DataArray(fin[c["invar"]].values * c["scl"] + c["off"], dims=("month", "lat", "lon"),
                       coords={"month": np.arange(1, 13), "lat": ilat, "lon": ilon})
    tin_p = xr.concat([tin.isel(lon=-1).assign_coords(lon=ilon[-1]-360.), tin,
                       tin.isel(lon=0).assign_coords(lon=ilon[0]+360.)], dim="lon")
    tin_r = tin_p.interp(lat=clat, lon=clon, method="linear")
    lm = ~np.isnan(tc.isel(month=0)); w = np.cos(np.deg2rad(clat))
    tc_ts = tc.where(lm).weighted(w).mean(("lat", "lon")).values
    tin_ts = tin_r.where(lm).weighted(w).mean(("lat", "lon")).values
    rmse = np.sqrt(np.nanmean((tin_ts - tc_ts) ** 2))
    tc_a = tc.where(lm).mean("month"); tin_a = tin_r.where(lm).mean("month")

    fig = plt.figure(figsize=(13, 8))
    gs = gridspec.GridSpec(2, 2, height_ratios=[1, 0.85], hspace=0.30, wspace=0.04)
    def mp(pos, d, t):
        dd, lon = add_cyclic_point(np.asarray(d), coord=clon.values)
        ax = fig.add_subplot(pos, projection=ccrs.PlateCarree())
        im = ax.pcolormesh(lon, clat, dd, cmap=c["cmap"], vmin=c["vmin"], vmax=c["vmax"],
                           shading="auto", transform=ccrs.PlateCarree())
        ax.coastlines(lw=0.5); ax.set_global()
        gl = ax.gridlines(draw_labels=True, lw=0.4, alpha=0.5, ls="--")
        gl.top_labels = False; gl.right_labels = False
        ax.set_title(t, fontsize=12); return ax, im
    axa, im = mp(gs[0, 0], tin_a, "(a) ERA5 forcing (input)")
    axb, im = mp(gs[0, 1], tc_a, "(b) CLM5 received")
    cb = fig.colorbar(im, ax=[axa, axb], orientation="horizontal", shrink=0.5,
                      aspect=40, pad=0.11, extend=c["ext"]); cb.set_label(f"{c['long']} ({c['unit']})")
    sub = gs[1, :].subgridspec(1, 3, width_ratios=[1, 4, 1])
    axc = fig.add_subplot(sub[0, 1]); mon = np.arange(1, 13)
    axc.plot(mon, tin_ts, "-s", color="tab:blue", ms=7, label="ERA5 (input)")
    axc.plot(mon, tc_ts, "--o", color="tab:red", ms=6, label="CLM5 (received)")
    axc.set_xlabel("month"); axc.set_ylabel(f"land-mean {VAR} ({c['unit']})")
    axc.set_xticks(range(1, 13)); axc.grid(alpha=0.3); axc.legend()
    axc.set_title(f"(c) Monthly {VAR} — RMSE={rmse:.3g} {c['unit']}")
    fig.suptitle(f"ERA5 → CLM transfer check: {VAR} 1980 (monthly-format)", fontsize=13, y=0.98)
    out = f"{FIG}/forcing_{VAR}_1980_monthly_fix.png"
    fig.savefig(out, dpi=140, bbox_inches="tight"); plt.close()
    print(f"{VAR}: input={np.nanmean(tin_ts):.2f}  CLM={np.nanmean(tc_ts):.2f}  RMSE={rmse:.3g}  -> {out.split('/')[-1]}")

import sys
_vars = sys.argv[1:] if len(sys.argv) > 1 else ["TBOT", "PRECT", "FLDS"]
for V in _vars:
    doplot(V)
