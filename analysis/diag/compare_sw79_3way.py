#!/usr/bin/env python3
"""3-way 1979 SW comparison: Ours(CLM FSDS) vs Chanhyuk(JULES SWdown) vs ERA5 raw(avg_sdswrf).
All 0.5deg monthly. Outputs: annual map (3 panels), JJA map (3 panels),
zonal-band monthly timeseries (equator +-5, 25-35N), each 3 lines."""
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

FD = "/Volumes/data01/MOF_LSM_project/data/forcing"
FIG = "/Volumes/data01/MOF_LSM_project/figures"
ch = xr.open_dataset(f"{FD}/ch_sw79_mon.nc")
lat = ch["lat"].values; lon = ch["lon"].values
DATA = {
    "Ours (CLM, hourly->6h avg)": xr.open_dataset(f"{FD}/fsds_mon_1979.nc")["FSDS"].values,
    "Chanhyuk (JULES, 6h)":       ch["SWdown"].values,
    "ERA5 raw (hourly mon-mean)": xr.open_dataset(f"{FD}/raw_sw79_mon.nc")["avg_sdswrf"].values,
}
w = np.cos(np.deg2rad(lat))[:, None]
def gmean(f):  # global cos-weighted, per month
    return np.array([np.nansum(f[m]*w)/np.nansum(w*np.isfinite(f[m])) for m in range(12)])

# ---- map helper ----
def map3(field_fn, title, fname, vmin=0, vmax=320):
    fig, axs = plt.subplots(1, 3, figsize=(17, 4.2),
                            subplot_kw={"projection": ccrs.PlateCarree()})
    for ax, (name, d) in zip(axs, DATA.items()):
        fld = field_fn(d)
        gm = np.nansum(fld*w)/np.nansum(w*np.isfinite(fld))
        im = ax.pcolormesh(lon, lat, fld, cmap="inferno", vmin=vmin, vmax=vmax,
                           transform=ccrs.PlateCarree(), shading="auto")
        ax.coastlines(lw=0.4); ax.set_title(f"{name}\n(global mean {gm:.1f} W/m²)", fontsize=10)
    fig.colorbar(im, ax=axs, orientation="horizontal", shrink=0.5, aspect=50, pad=0.06,
                 extend="max", label="SW down (W/m²)")
    fig.suptitle(title, fontsize=13, y=1.02)
    out = f"{FIG}/{fname}"; fig.savefig(out, dpi=140, bbox_inches="tight"); plt.close()
    print("saved:", fname)

map3(lambda d: d.mean(0), "1979 annual-mean downward SW", "sw79_annmap_3way.png")
map3(lambda d: d[5:8].mean(0), "1979 JJA-mean downward SW", "sw79_jjamap_3way.png")

# ---- zonal-band monthly timeseries ----
def band_ts(d, lo, hi):
    m = (lat >= lo) & (lat < hi)
    ww = w[m]
    return np.array([np.nansum(d[t, m, :]*ww)/np.nansum((ww*np.ones((m.sum(), d.shape[2])))*np.isfinite(d[t, m, :]))
                     for t in range(12)])

bands = [("Equator ±5°", -5, 5), ("25–35°N", 25, 35)]
fig, axs = plt.subplots(1, 2, figsize=(14, 5))
mon = np.arange(1, 13)
colors = {"Ours (CLM, hourly->6h avg)": "tab:red", "Chanhyuk (JULES, 6h)": "tab:green",
          "ERA5 raw (hourly mon-mean)": "tab:blue"}
styles = {"Ours (CLM, hourly->6h avg)": "-s", "Chanhyuk (JULES, 6h)": "-o",
          "ERA5 raw (hourly mon-mean)": "-^"}
for ax, (bname, lo, hi) in zip(axs, bands):
    for name, d in DATA.items():
        ts = band_ts(d, lo, hi)
        ax.plot(mon, ts, styles[name], color=colors[name], ms=5, label=name)
    ax.set_title(f"{bname}  monthly SW"); ax.set_xlabel("month")
    ax.set_ylabel("SW down (W/m²)"); ax.set_xticks(range(1, 13)); ax.grid(alpha=0.3)
axs[0].legend(fontsize=8)
fig.suptitle("1979 downward SW — zonal-band monthly mean (3-way)", fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.96])
out = f"{FIG}/sw79_ts_3way.png"; fig.savefig(out, dpi=140, bbox_inches="tight"); plt.close()
print("saved: sw79_ts_3way.png")

# console summary
print("\n=== global-mean annual ===")
for name, d in DATA.items():
    print(f"  {name}: {gmean(d).mean():.2f} W/m²")
print("=== Equator ±5 monthly ===")
for name, d in DATA.items():
    print(f"  {name}: {np.round(band_ts(d,-5,5),0)}")
