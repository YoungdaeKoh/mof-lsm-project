#!/usr/bin/env python3
"""
CLM5 vs ERA5-Land soil temperature & moisture — monthly time series, 1979-1987,
global land, ERA5-Land 4 layers (L1 0-7, L2 7-28, L3 28-100, L4 100-289 cm).
Layout:
  (a) CLM5 soil temperature TSOI     (b) ERA5-Land soil temperature stl1-4
  (c) CLM5 soil moisture  H2OSOI     (d) ERA5-Land soil moisture  swvl1-4
ERA5-Land soil-temp (stl) must be regridded to CLM grid first (era5land_stl_clmgrid_*.nc);
if absent, panel (b) is annotated as pending.
"""
import glob
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

CLM_DIR = "/Volumes/data01/MOF_LSM_project/cesm/clm_output/I2000_ERA5_spinup/lnd/hist"
ERA5L_DIR = "/Volumes/data01/MOF_LSM_project/data/era5land"
FIGDIR  = "/Volumes/data01/MOF_LSM_project/figures"

LAYER_MAP = {
    "L1 (0-7cm)":     [0, 1],
    "L2 (7-28cm)":    [2, 3, 4],
    "L3 (28-100cm)":  [5, 6, 7],
    "L4 (100-289cm)": [8, 9, 10, 11, 12],
}
COLORS = ["tab:red", "tab:orange", "tab:green", "tab:blue"]

def layer_thickness(z_cm):
    z = np.asarray(z_cm, float); zi = np.empty(len(z)+1)
    zi[0] = 0.0; zi[1:-1] = 0.5*(z[:-1]+z[1:]); zi[-1] = z[-1] + (z[-1]-zi[-2])
    return np.diff(zi)

# ---------- CLM5 ----------
ds = xr.open_mfdataset(sorted(glob.glob(f"{CLM_DIR}/*.clm2.h0.*.nc")),
                       combine="by_coords", use_cftime=True, decode_timedelta=False)
nt = ds.sizes["time"]
w  = np.cos(np.deg2rad(ds["lat"]))
dz = layer_thickness(ds["levgrnd"].values * 100.0)
land = ~np.isnan(ds["H2OSOI"].isel(levsoi=0, time=0))
zdim = {"TSOI": "levgrnd", "H2OSOI": "levsoi"}

def clm_layered(var):
    da = ds[var].where(land); ld = zdim[var]; out = {}
    for name, idx in LAYER_MAP.items():
        prof = (da.isel({ld: idx}) * xr.DataArray(dz[idx], dims=ld)).sum(ld, skipna=False) / dz[idx].sum()
        out[name] = prof.weighted(w).mean(("lat","lon"), skipna=True).values
    return out

clm_t = {k: v-273.15 for k, v in clm_layered("TSOI").items()}
clm_m = clm_layered("H2OSOI")

# ---------- ERA5-Land ----------
def era5land(pattern, vlist, off=0.0):
    files = sorted(glob.glob(f"{ERA5L_DIR}/{pattern}"))
    if not files: return None
    de = xr.open_mfdataset(files, combine="nested", concat_dim="time", decode_timedelta=False)
    we = np.cos(np.deg2rad(de["lat"]))
    return {name: (de[v]+off).weighted(we).mean(("lat","lon"), skipna=True).values
            for name, v in zip(LAYER_MAP, vlist)}

era_m = era5land("era5land_swvl_clmgrid_*.nc", ["swvl1","swvl2","swvl3","swvl4"])
era_t = era5land("era5land_stl_clmgrid_*.nc",  ["stl1","stl2","stl3","stl4"], off=-273.15)

# ---------- plot ----------
mon = np.arange(nt)
fig, axs = plt.subplots(2, 2, figsize=(15, 9), sharex=True)
def draw(ax, data, title, ylab, pending=False):
    if data is None:
        ax.text(0.5, 0.5, "ERA5-Land soil temp\n(stl) regrid pending", ha="center", va="center",
                transform=ax.transAxes, fontsize=14, color="grey")
    else:
        for name, col in zip(LAYER_MAP, COLORS):
            ax.plot(mon, data[name], color=col, lw=1.5, label=name)
        ax.legend(ncol=2, fontsize=11, loc="upper right")
    ax.set_title(title, fontsize=15); ax.set_ylabel(ylab, fontsize=14)
    ax.grid(alpha=0.3); ax.tick_params(labelsize=12)
    for y in range(0, nt+1, 12): ax.axvline(y, color="grey", lw=0.3, alpha=0.5)

draw(axs[0,0], clm_t, "(a) CLM5 soil temperature  TSOI",     "soil temp (°C)")
draw(axs[0,1], era_t, "(b) ERA5-Land soil temperature",      "soil temp (°C)")
draw(axs[1,0], clm_m, "(c) CLM5 soil moisture  H2OSOI",      "soil moisture (m³/m³)")
draw(axs[1,1], era_m, "(d) ERA5-Land soil moisture  swvl",   "soil moisture (m³/m³)")

# share y-limits within each row for fair comparison
for r in range(2):
    lo = min(axs[r,0].get_ylim()[0], axs[r,1].get_ylim()[0])
    hi = max(axs[r,0].get_ylim()[1], axs[r,1].get_ylim()[1])
    axs[r,0].set_ylim(lo, hi); axs[r,1].set_ylim(lo, hi)
for c in range(2):
    axs[1,c].set_xlabel("year", fontsize=14)
    axs[1,c].set_xticks(range(0, nt+1, 12)); axs[1,c].set_xticklabels([f"{1979+i}" for i in range(10)])
fig.suptitle("CLM5 vs ERA5-Land — soil temperature & moisture, monthly 1979-1987 (global land, ERA5-Land 4 layers)",
             fontsize=15)
fig.tight_layout()
out = f"{FIGDIR}/soil_clm_vs_era5land.png"
fig.savefig(out, dpi=140)
print("saved:", out)
print("ERA5-Land moisture:", "OK" if era_m is not None else "MISSING",
      "| ERA5-Land soiltemp:", "OK" if era_t is not None else "MISSING (regrid stl1-4)")
