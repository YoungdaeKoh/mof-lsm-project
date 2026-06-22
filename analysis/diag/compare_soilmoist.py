#!/usr/bin/env python3
"""
Layered soil-moisture comparison: CLM5 (H2OSOI) vs ERA5-Land (swvl1-4).
First figure: global-land area-mean seasonal cycle, 4 matched depth layers.

CLM side works now (local h0). ERA5-Land side reads the regridded file
(produced by regrid_era5land_swvl.ncl on the server) once available.

Run: python3 compare_soilmoist.py
"""
import glob
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

CLM_DIR  = "/Volumes/data01/MOF_LSM_project/cesm/clm_output/I2000_ERA5_spinup/lnd/hist"
ERA5L    = "/Volumes/data01/MOF_LSM_project/data/era5land/era5land_swvl_clmgrid_*.nc"  # after rsync
FIGDIR   = "/Volumes/data01/MOF_LSM_project/figures"

# ERA5-Land 4 layers (depth range cm) -> CLM levsoi indices (node depth cm)
#   levsoi node(cm): 1,4,9,16,26,40,58,80,106,136,170,208,250,...
LAYER_MAP = {
    "L1 (0-7cm)":     [0, 1],
    "L2 (7-28cm)":    [2, 3, 4],
    "L3 (28-100cm)":  [5, 6, 7],
    "L4 (100-289cm)": [8, 9, 10, 11, 12],
}
ERA5L_VARS = ["swvl1", "swvl2", "swvl3", "swvl4"]


def clm_layer_thickness(levgrnd_cm):
    """Approx layer thickness (cm) from node depths: interfaces at midpoints."""
    z = np.asarray(levgrnd_cm, float)
    zi = np.empty(len(z) + 1)
    zi[0] = 0.0
    zi[1:-1] = 0.5 * (z[:-1] + z[1:])
    zi[-1] = z[-1] + (z[-1] - zi[-2])
    return np.diff(zi)  # dz per layer


def clm_layered_seasonal_cycle():
    """Return dict layer-> (12,) global-land area-mean H2OSOI climatology."""
    files = sorted(glob.glob(f"{CLM_DIR}/*.clm2.h0.*.nc"))
    print(f"CLM files: {len(files)}")
    # model years 0001-0006 are < pandas datetime min (1677) -> use cftime
    ds = xr.open_mfdataset(files, combine="by_coords",
                           use_cftime=True, decode_timedelta=False)
    h2o = ds["H2OSOI"]                      # (time, levsoi, lat, lon), mm3/mm3
    lev_cm = ds["levgrnd"].values[:20] * 100.0   # levsoi nodes in cm
    dz = clm_layer_thickness(lev_cm)             # (20,) cm

    # area weight: cos(lat)
    w = np.cos(np.deg2rad(ds["lat"]))
    out = {}
    for name, idx in LAYER_MAP.items():
        sub = h2o.isel(levsoi=idx)                       # (time, k, lat, lon)
        wk = xr.DataArray(dz[idx], dims="levsoi")        # thickness weights
        prof = (sub * wk).sum("levsoi") / wk.sum()        # depth-weighted -> (time,lat,lon)
        # global land area-mean (mask handled by NaN/_FillValue)
        am = prof.weighted(w).mean(("lat", "lon"))        # (time,)
        clim = am.groupby("time.month").mean().values     # (12,)
        out[name] = clim
        print(f"  {name}: ann mean = {np.nanmean(clim):.3f} m3/m3")
    return out


def era5land_layered_seasonal_cycle():
    """Return dict layer-> (12,) from regridded ERA5-Land (if available)."""
    files = sorted(glob.glob(ERA5L))
    if not files:
        print("ERA5-Land regridded files not found yet -> skip")
        return None
    # regridded files have a 'time' dim (12 months) but no time coordinate
    # -> nested concat along time; reshape (nyear,12) for month climatology
    ds = xr.open_mfdataset(files, combine="nested", concat_dim="time")
    w = np.cos(np.deg2rad(ds["lat"]))
    out = {}
    for name, var in zip(LAYER_MAP.keys(), ERA5L_VARS):
        am = ds[var].weighted(w).mean(("lat", "lon")).values   # (nyear*12,)
        clim = am.reshape(-1, 12).mean(axis=0)                  # (12,)
        out[name] = clim
        print(f"  ERA5-Land {name}: ann mean = {np.nanmean(clim):.3f} m3/m3")
    return out


def main():
    clm = clm_layered_seasonal_cycle()
    era = era5land_layered_seasonal_cycle()
    mon = np.arange(1, 13)

    # --- (1) absolute ---
    fig, axs = plt.subplots(2, 2, figsize=(11, 8), sharex=True)
    for ax, name in zip(axs.ravel(), LAYER_MAP.keys()):
        ax.plot(mon, clm[name], "-o", color="tab:red", label="CLM5")
        if era is not None:
            ax.plot(mon, era[name], "-s", color="tab:blue", label="ERA5-Land")
        ax.set_title(name); ax.set_xlabel("month")
        ax.set_ylabel("soil moisture (m$^3$/m$^3$)")
        ax.grid(alpha=0.3); ax.legend()
    fig.suptitle("Global-land soil moisture seasonal cycle (1979-1987)\n"
                 "CLM5 (H2OSOI, depth-weighted) vs ERA5-Land  [absolute]")
    fig.tight_layout()
    fig.savefig(f"{FIGDIR}/soilmoist_seasonal_layered.png", dpi=130)

    # --- (2) anomaly: deviation from annual mean (fair phase/amplitude) ---
    fig, axs = plt.subplots(2, 2, figsize=(11, 8), sharex=True)
    for ax, name in zip(axs.ravel(), LAYER_MAP.keys()):
        ca = clm[name] - np.nanmean(clm[name])
        ax.plot(mon, ca, "-o", color="tab:red", label="CLM5")
        if era is not None:
            ea = era[name] - np.nanmean(era[name])
            ax.plot(mon, ea, "-s", color="tab:blue", label="ERA5-Land")
        ax.axhline(0, color="grey", lw=0.6)
        ax.set_title(name); ax.set_xlabel("month")
        ax.set_ylabel("anomaly (m$^3$/m$^3$)")
        ax.grid(alpha=0.3); ax.legend()
    fig.suptitle("Soil moisture seasonal ANOMALY (− annual mean), 1979-1987\n"
                 "phase & amplitude comparison (offset removed)")
    fig.tight_layout()
    fig.savefig(f"{FIGDIR}/soilmoist_seasonal_anomaly.png", dpi=130)

    # amplitude (max-min) print
    print("\nseasonal amplitude (max-min, m3/m3):")
    for name in LAYER_MAP:
        a_clm = np.nanmax(clm[name]) - np.nanmin(clm[name])
        a_era = (np.nanmax(era[name]) - np.nanmin(era[name])) if era else np.nan
        print(f"  {name}: CLM={a_clm:.4f}  ERA5-Land={a_era:.4f}  ratio={a_clm/a_era:.2f}")
    print("saved both figures to", FIGDIR)


if __name__ == "__main__":
    main()
