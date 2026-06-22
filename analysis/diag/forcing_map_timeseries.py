#!/usr/bin/env python3
"""
Forcing transfer check (1979): input ERA5 forcing vs CLM-received.
Input (0.5°) regridded to CLM f19 grid; CLM land mask; full globe (incl Antarctica).
 (a) input map  (b) CLM map  (c) global-land monthly time series.
Variable selectable:  python forcing_map_timeseries.py [TBOT|PRECT|FSDS|FLDS]
"""
import sys, glob
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib import gridspec
try:
    import cartopy.crs as ccrs
    from cartopy.util import add_cyclic_point
    HAS = True
except Exception:
    HAS = False

FORC = "/Volumes/data01/MOF_LSM_project/data/forcing/era5_1979_annmean.nc"  # 12 mon, 0.5°
CLM_DIR = "/Volumes/data01/MOF_LSM_project/cesm/clm_output/I2000_ERA5_spinup/lnd/hist"
FIGDIR  = "/Volumes/data01/MOF_LSM_project/figures"
ANT = -90.0   # include Antarctica (full globe)

# per-variable config: input var, offset/scale (->display unit), CLM expr, plot opts
CFG = {
    "TBOT":  dict(invar="TBOT",     off=-273.15, scl=1.0,    clm=["TBOT"],         clmoff=-273.15, clmscl=1.0,
                  cmap="RdYlBu_r", vmin=-35, vmax=35, ext="both", c0=0,    unit="°C",     fmt=".2f",
                  long="2m air temperature  TBOT", tag="TBOT"),
    "PRECT": dict(invar="PRECTmms", off=0.0,    scl=86400., clm=["RAIN","SNOW"],  clmoff=0.0,    clmscl=86400.,
                  cmap="YlGnBu",   vmin=0,   vmax=10, ext="max", c0=None, unit="mm/day", fmt=".3f",
                  long="Precipitation  RAIN+SNOW", tag="PRECT"),
    "FSDS":  dict(invar="FSDS",     off=0.0,    scl=1.0,    clm=["FSDS"],         clmoff=0.0,    clmscl=1.0,
                  cmap="inferno",  vmin=0,   vmax=320, ext="max", c0=None, unit="W/m²",  fmt=".2f",
                  long="Downward shortwave  FSDS", tag="FSDS"),
    "FLDS":  dict(invar="FLDS",     off=0.0,    scl=1.0,    clm=["FLDS"],         clmoff=0.0,    clmscl=1.0,
                  cmap="magma",    vmin=150, vmax=450, ext="both", c0=None, unit="W/m²", fmt=".2f",
                  long="Downward longwave  FLDS", tag="FLDS"),
    "WIND":  dict(invar="WIND",     off=0.0,    scl=1.0,    clm=["WIND"],         clmoff=0.0,    clmscl=1.0,
                  cmap="viridis",  vmin=0,   vmax=12, ext="max", c0=None, unit="m/s",  fmt=".3f",
                  long="Wind speed  WIND", tag="WIND"),
}
VAR = sys.argv[1] if len(sys.argv) > 1 else "TBOT"
c = CFG[VAR]

# --- CLM received (f19), model yr 0001 = 1979 ---
dc = xr.open_mfdataset(sorted(glob.glob(f"{CLM_DIR}/*.clm2.h0.0001-*.nc")),
                       combine="by_coords", use_cftime=True, decode_timedelta=False)
tc_raw = sum(dc[v] for v in c["clm"])                       # RAIN+SNOW or single var
tc = (tc_raw * c["clmscl"] + c["clmoff"]).load()
tc = tc.assign_coords(month=("time", np.arange(1, 13))).swap_dims({"time": "month"})
clat = dc["lat"]; clon = dc["lon"]

# --- input forcing (0.5°), 1D coords, regrid to CLM grid ---
fi = xr.open_dataset(FORC)
ilat = fi["LATIXY"].values[:, 0]
ilon = fi["LONGXY"].values[0, :]
tin = xr.DataArray((fi[c["invar"]].values * c["scl"] + c["off"]),
                   dims=("month", "lat", "lon"),
                   coords={"month": np.arange(1, 13), "lat": ilat, "lon": ilon})
# periodic lon so clon=0 (outside 0.25..359.75) isn't a NaN seam
tin_p = xr.concat([tin.isel(lon=-1).assign_coords(lon=ilon[-1]-360.),
                   tin,
                   tin.isel(lon=0).assign_coords(lon=ilon[0]+360.)], dim="lon")
tin_r = tin_p.interp(lat=clat, lon=clon, method="linear")

# --- common mask: CLM land AND lat>=ANT ---
landmask = (~np.isnan(tc.isel(month=0))) & (clat >= ANT)
tc_m  = tc.where(landmask)
tin_m = tin_r.where(landmask)
tc_ann  = tc_m.mean("month"); tin_ann = tin_m.mean("month")
wlat = np.cos(np.deg2rad(clat))
tc_ts  = tc_m.weighted(wlat).mean(("lat", "lon")).values
tin_ts = tin_m.weighted(wlat).mean(("lat", "lon")).values

# --- plot ---
fig = plt.figure(figsize=(13, 8))
gs = gridspec.GridSpec(2, 2, height_ratios=[1, 0.85], hspace=0.30, wspace=0.04)
def mp(pos, data, title):
    d = np.asarray(data); lon = clon.values
    if HAS:
        d, lon = add_cyclic_point(d, coord=clon.values)
        ax = fig.add_subplot(pos, projection=ccrs.PlateCarree(central_longitude=0))
        tr = ccrs.PlateCarree()
        im = ax.pcolormesh(lon, clat, d, cmap=c["cmap"], vmin=c["vmin"], vmax=c["vmax"],
                           shading="auto", transform=tr)
        if c["c0"] is not None:
            ax.contour(lon, clat, d, levels=[c["c0"]], colors="k", linewidths=1.1, transform=tr)
        ax.coastlines(lw=0.5); ax.set_global()
        gl = ax.gridlines(draw_labels=True, lw=0.4, color="grey", alpha=0.5, ls="--")
        gl.top_labels = False; gl.right_labels = False
        gl.xlabel_style = {"size": 11}; gl.ylabel_style = {"size": 11}
    else:
        ax = fig.add_subplot(pos)
        im = ax.pcolormesh(lon, clat, d, cmap=c["cmap"], vmin=c["vmin"], vmax=c["vmax"], shading="auto")
    ax.set_title(title, fontsize=12); return ax, im
axa, im = mp(gs[0,0], tin_ann, "(a) ERA5 forcing (input)")
axb, im = mp(gs[0,1], tc_ann,  "(b) CLM5 received (output)")
cb = fig.colorbar(im, ax=[axa, axb], orientation="horizontal",
                  shrink=0.5, aspect=40, pad=0.11, extend=c["ext"])
cb.set_label(f"{c['long']} ({c['unit']})")

sub = gs[1,:].subgridspec(1, 3, width_ratios=[1, 4, 1])
axc = fig.add_subplot(sub[0,1])
mon = np.arange(1,13)
axc.plot(mon, tin_ts, "-s", color="tab:blue", ms=7, label="ERA5")
axc.plot(mon, tc_ts,  "--o", color="tab:red", ms=6, label="CLM5")
axc.set_xlabel("month", fontsize=13); axc.set_ylabel(f"land-mean {c['tag']} ({c['unit']})", fontsize=13)
axc.tick_params(labelsize=11)
axc.set_xticks(range(1,13)); axc.grid(alpha=0.3); axc.legend(fontsize=11)
rmse = np.sqrt(np.nanmean((tin_ts-tc_ts)**2))
axc.set_title(f"(c) Monthly {c['tag']} — RMSE={rmse:{c['fmt']}} {c['unit']}")
fig.suptitle(f"ERA5 forcing → CLM transfer check: {c['tag']} (1979)", fontsize=13, y=0.98)
out = f"{FIGDIR}/forcing_{c['tag']}_map_ts.png"
fig.savefig(out, dpi=140, bbox_inches="tight")
print("saved:", out)
print(f"land-mean {c['tag']}: input={np.nanmean(tin_ts):.3f}  CLM={np.nanmean(tc_ts):.3f}  RMSE={rmse:.4f}")
