#!/usr/bin/env python3
"""
CLM5 soil temperature (TSOI) & soil moisture (H2OSOI) monthly time series,
9 years (1979-1987 = model 0001-0009, 108 months), depth-aggregated to the
4 ERA5-Land (H-TESSEL) layers for direct comparison:
  L1 0-7cm, L2 7-28cm, L3 28-100cm, L4 100-289cm  (depth-weighted CLM layers).
"""
import glob
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

CLM_DIR = "/Volumes/data01/MOF_LSM_project/cesm/clm_output/I2000_ERA5_spinup/lnd/hist"
FIGDIR  = "/Volumes/data01/MOF_LSM_project/figures"

# ERA5-Land 4 layers -> CLM level indices (node depth cm: 1,4,9,16,26,40,58,80,106,136,170,208,250)
LAYER_MAP = {
    "L1 (0-7cm)":     [0, 1],
    "L2 (7-28cm)":    [2, 3, 4],
    "L3 (28-100cm)":  [5, 6, 7],
    "L4 (100-289cm)": [8, 9, 10, 11, 12],
}
COLORS = ["tab:red", "tab:orange", "tab:green", "tab:blue"]

def layer_thickness(z_cm):
    """Approx CLM layer thickness (cm) from node depths: interfaces at midpoints."""
    z = np.asarray(z_cm, float); zi = np.empty(len(z)+1)
    zi[0] = 0.0; zi[1:-1] = 0.5*(z[:-1]+z[1:]); zi[-1] = z[-1] + (z[-1]-zi[-2])
    return np.diff(zi)

ds = xr.open_mfdataset(sorted(glob.glob(f"{CLM_DIR}/*.clm2.h0.*.nc")),
                       combine="by_coords", use_cftime=True, decode_timedelta=False)
nt = ds.sizes["time"]
w  = np.cos(np.deg2rad(ds["lat"]))
z_cm = ds["levgrnd"].values * 100.0
dz   = layer_thickness(z_cm)                      # (25,) cm
zdim = {"TSOI": "levgrnd", "H2OSOI": "levsoi"}
# land mask: H2OSOI is NaN over ocean; TSOI is 0 K over ocean -> use H2OSOI to mask both
land = ~np.isnan(ds["H2OSOI"].isel(levsoi=0, time=0))

def layered_ts(var):
    """dict layer -> (nt,) global-land area-mean, depth-weighted into 4 ERA5-Land layers."""
    da = ds[var].where(land); ld = zdim[var]
    out = {}
    for name, idx in LAYER_MAP.items():
        sub = da.isel({ld: idx})
        wk  = xr.DataArray(dz[idx], dims=ld)
        prof = (sub*wk).sum(ld, skipna=False) / wk.sum()   # ocean stays NaN (no 0 fill)
        out[name] = prof.weighted(w).mean(("lat","lon"), skipna=True).values
    return out

tsoi = {k: v-273.15 for k, v in layered_ts("TSOI").items()}
h2o  = layered_ts("H2OSOI")
mon  = np.arange(nt)

fig, axs = plt.subplots(2, 1, figsize=(8.7, 8), sharex=True)
for name, col in zip(LAYER_MAP, COLORS):
    axs[0].plot(mon, tsoi[name], color=col, lw=1.5, label=name)
    axs[1].plot(mon, h2o[name],  color=col, lw=1.5, label=name)
axs[0].set_title("(a) CLM5 monthly soil temperature (TSOI, global-land)", fontsize=15)
axs[0].set_ylabel("soil temp (°C)", fontsize=15)
axs[1].set_title("(c) CLM5 monthly soil moisture (H2OSOI, global)", fontsize=15)
axs[1].set_ylabel("soil moisture (m³/m³)", fontsize=15)
for ax in axs:
    ax.grid(alpha=0.3); ax.legend(ncol=2, fontsize=12, loc="upper right")
    ax.tick_params(labelsize=13)
    for y in range(0, nt+1, 12): ax.axvline(y, color="grey", lw=0.3, alpha=0.5)
axs[1].set_xlabel("year", fontsize=15)
axs[1].set_xticks(range(0, nt+1, 12)); axs[1].set_xticklabels([f"{1979+i}" for i in range(10)])
fig.suptitle("CLM5 soil temperature & moisture — monthly 1979-1987\n(global land, ERA5-Land depths)", fontsize=15)
fig.tight_layout()
out = f"{FIGDIR}/soil_layered_timeseries.png"
fig.savefig(out, dpi=140)
print("saved:", out)
for name in LAYER_MAP:
    print(f"{name:16s} TSOI {tsoi[name].mean():6.2f}°C  H2OSOI {h2o[name].mean():.3f} m3/m3")
