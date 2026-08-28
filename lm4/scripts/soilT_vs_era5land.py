"""Soil temperature, LM4+ against ERA5-Land, on the four ERA5-Land layers.

The data section of the year-one report claims soil temperature holdings; this
is the comparison that uses them.  LM4's twenty layers were folded onto the four
ERA5-Land layers by overlap-weighted averaging beforehand
(extract_soilT_era5layers.py) -- matching by nearest node would compare slabs of
different thickness, and thickness alone changes the seasonal amplitude.

Two things are reported, and the second matters more than the first:

  * annual mean bias, which mostly reflects the forcing air temperature
  * the amplitude of the climatological annual cycle, which reflects how the
    model moves heat downward.  A soil column that damps the surface signal too
    little or too much shows up here even when its mean is right, and it is the
    quantity that governs how long a deep column takes to spin up.

ERA5-Land is a reanalysis in the loose sense only: it is H-TESSEL forced by ERA5
without land data assimilation, so this is a model-to-model comparison against a
well-tested reference, not a validation against observation.  There is no global
gridded soil temperature observation to do better with.

Both fields are binned to a common 1-degree grid by their own coordinates
(never by reshape -- ERA5-Land carries 1801 latitudes including both poles).

Inputs : lm4/data/soilT_era5layers_1982_2010.npz
         /Volumes/data02/ERA5L_soilT/stl{1..4}/ERA5m-land_YYYYMM.nc
Output : figures/soilT_vs_era5land.png, lm4/data/soilT_vs_era5land.csv
"""
import glob
import os
import sys
import numpy as np
import netCDF4 as nc
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

sys.path.insert(0, "lm4/scripts")
from greenland_mask import in_greenland

ERA5DIR = "/Volumes/data02/ERA5L_soilT"
YEARS = np.arange(1982, 2011)
NLAT, NLON = 180, 360
lat1 = 89.5 - np.arange(NLAT)          # descending
lon1 = -179.5 + np.arange(NLON)
LAYERS = [("0–7 cm", "stl1"), ("7–28 cm", "stl2"),
          ("28–100 cm", "stl3"), ("100–289 cm", "stl4")]

# ------------------------------------------------------------------- LM4 ----
z = np.load("lm4/data/soilT_era5layers_1982_2010.npz")
mlat, mlon, soil = z["lat"], z["lon"], z["soil"]
keep = soil & ~in_greenland(mlat, mlon)
ilat = np.clip(((90.0 - mlat) / 1.0).astype(int), 0, NLAT - 1)
ilon = np.clip(((mlon + 180.0) / 1.0).astype(int), 0, NLON - 1)
soilT = z["soilT"]                      # (year, month, layer, point)


def bin_points(v):
    v = np.where(keep, v, np.nan)
    s = np.zeros((NLAT, NLON))
    c = np.zeros((NLAT, NLON))
    ok = np.isfinite(v)
    np.add.at(s, (ilat[ok], ilon[ok]), v[ok])
    np.add.at(c, (ilat[ok], ilon[ok]), 1.0)
    out = np.full((NLAT, NLON), np.nan)
    m = c > 0
    out[m] = s[m] / c[m]
    return out


# monthly climatology, then annual mean and amplitude
lm_clim = np.stack([[bin_points(np.nanmean(soilT[:, m, k, :], axis=0))
                     for m in range(12)] for k in range(4)])   # (layer, month, y, x)
print("LM4 binned:", lm_clim.shape)

# ------------------------------------------------------------- ERA5-Land ----
def era5_clim(var):
    """Monthly climatology on the 1-degree grid, binned by coordinate."""
    acc = np.zeros((12, NLAT, NLON))
    cnt = np.zeros((12, NLAT, NLON))
    files = sorted(glob.glob("%s/%s/ERA5m-land_*.nc" % (ERA5DIR, var)))
    files = [f for f in files
             if YEARS[0] <= int(os.path.basename(f)[11:15]) <= YEARS[-1]]
    if not files:
        raise SystemExit("no files for %s" % var)
    idx = None
    for f in files:
        m = int(os.path.basename(f)[15:17]) - 1
        d = nc.Dataset(f)
        if idx is None:
            sla = np.array(d.variables["latitude"][:], "f8")
            slo = np.array(d.variables["longitude"][:], "f8")
            slo = np.where(slo > 180, slo - 360, slo)
            jj = np.clip(((90.0 - sla) / 1.0).astype(int), 0, NLAT - 1)
            ii = np.clip(((slo + 180.0) / 1.0).astype(int), 0, NLON - 1)
            idx = (jj[:, None] * NLON + ii[None, :]).ravel()
        a = np.ma.filled(d.variables[var][0].astype("f8"), np.nan)
        d.close()
        good = np.isfinite(a).ravel()
        s = np.zeros(NLAT * NLON)
        c = np.zeros(NLAT * NLON)
        np.add.at(s, idx[good], a.ravel()[good])
        np.add.at(c, idx[good], 1.0)
        acc[m] += s.reshape(NLAT, NLON)
        cnt[m] += c.reshape(NLAT, NLON)
    with np.errstate(invalid="ignore"):
        out = np.where(cnt > 0, acc / np.maximum(cnt, 1), np.nan)
    print("  %s: %d files" % (var, len(files)))
    return out


CACHE = "lm4/data/soilT_clim_1deg.npz"
try:
    c = np.load(CACHE)
    er_clim = c["era5"]
    print("loaded ERA5-Land climatology cache: %s" % CACHE)
except FileNotFoundError:
    # 1,008 files at 0.1 deg; cache so that report variants of this figure are free
    er_clim = np.stack([era5_clim(v) for _, v in LAYERS])      # (layer, month, y, x)
    np.savez_compressed(CACHE, era5=er_clim.astype("f4"), lm4=lm_clim.astype("f4"))
    print("cached to %s" % CACHE)

# ------------------------------------------------------------------ scores --
W = np.cos(np.deg2rad(lat1))[:, None] * np.ones((1, NLON))
rows = []
print("\n%-12s %7s %8s %8s %7s %7s %9s %9s" %
      ("layer", "cells", "LM4 K", "ERA5 K", "bias", "RMSE", "r", "amp ratio"))
for k, (name, _) in enumerate(LAYERS):
    m_ann, e_ann = lm_clim[k].mean(axis=0), er_clim[k].mean(axis=0)
    m_amp = lm_clim[k].max(axis=0) - lm_clim[k].min(axis=0)
    e_amp = er_clim[k].max(axis=0) - er_clim[k].min(axis=0)
    s = np.isfinite(m_ann) & np.isfinite(e_ann)
    w = np.where(s, W, 0.0)
    mm = np.nansum(np.where(s, m_ann, 0) * w) / w.sum()
    ee = np.nansum(np.where(s, e_ann, 0) * w) / w.sum()
    rmse = np.sqrt(np.nansum(np.where(s, (m_ann - e_ann) ** 2, 0) * w) / w.sum())
    r = np.corrcoef(m_ann[s], e_ann[s])[0, 1]
    ma = np.nansum(np.where(s, m_amp, 0) * w) / w.sum()
    ea = np.nansum(np.where(s, e_amp, 0) * w) / w.sum()
    print("%-12s %7d %8.2f %8.2f %+7.2f %7.2f %9.3f %9.3f"
          % (name, s.sum(), mm, ee, mm - ee, rmse, r, ma / ea))
    rows.append([k + 1, s.sum(), mm, ee, mm - ee, rmse, r, ma, ea])
    if k == 0:
        common, bias0 = s, m_ann - e_ann
    globals()["L%d" % k] = (m_ann, e_ann, s, m_amp, e_amp)

np.savetxt("lm4/data/soilT_vs_era5land.csv", np.array(rows), delimiter=",",
           header="layer,ncells,lm4_K,era5_K,bias_K,rmse_K,r,lm4_amp_K,era5_amp_K",
           comments="", fmt="%.5f")

# latitude bands, deepest layer -- the one that governs spin-up
print("\n100–289 cm by latitude band")
m_ann, e_ann, s, m_amp, e_amp = L3
print("%-10s %8s %8s %8s %10s" % ("band", "LM4", "ERA5", "bias", "amp ratio"))
for a0, a1 in ((60, 85), (30, 60), (0, 30), (-30, 0), (-60, -30)):
    b = s & (lat1[:, None] >= a0) & (lat1[:, None] < a1)
    if b.sum() < 20:
        continue
    w = np.where(b, W, 0.0)
    mm = np.nansum(np.where(b, m_ann, 0) * w) / w.sum()
    ee = np.nansum(np.where(b, e_ann, 0) * w) / w.sum()
    ma = np.nansum(np.where(b, m_amp, 0) * w) / w.sum()
    ea = np.nansum(np.where(b, e_amp, 0) * w) / w.sum()
    print("%4d..%-4d %8.2f %8.2f %+8.2f %10.3f" % (a0, a1, mm, ee, mm - ee, ma / ea))

# ------------------------------------------------------------------ figure --
proj = ccrs.PlateCarree()
fig, axes = plt.subplots(2, 4, figsize=(21, 8.4), subplot_kw={"projection": proj},
                         constrained_layout=True)
LVB = np.array([-8, -5, -3, -2, -1, 1, 2, 3, 5, 8])
LVA = np.array([0.5, 0.7, 0.8, 0.9, 0.95, 1.05, 1.1, 1.2, 1.4, 1.8])
for k, (name, _) in enumerate(LAYERS):
    m_ann, e_ann, s, m_amp, e_amp = globals()["L%d" % k]
    for r_, (fld, lv, cmap, lab) in enumerate((
            (np.where(s, m_ann - e_ann, np.nan), LVB, "RdBu_r", "annual mean bias [K]"),
            (np.where(s & (e_amp > 0.5), m_amp / e_amp, np.nan), LVA, "PuOr_r",
             "annual amplitude, model / ERA5-Land"))):
        ax = axes[r_, k]
        ax.set_extent([-180, 180, -58, 84], crs=proj)
        ax.add_feature(cfeature.COASTLINE, lw=0.4)
        im = ax.contourf(lon1, lat1, fld, levels=lv, cmap=cmap, extend="both",
                         transform=proj)
        ax.set_title("%s   %s" % (name, "bias" if r_ == 0 else "amplitude"),
                     fontsize=13)
        gl = ax.gridlines(draw_labels=(k == 0), lw=0.3, alpha=0.4)
        gl.top_labels = False
        gl.right_labels = False
        if k == 3:
            cb = fig.colorbar(im, ax=axes[r_, :], orientation="vertical",
                              ticks=lv, shrink=0.85, pad=0.01, aspect=25)
            cb.set_label(lab, fontsize=12)

fig.suptitle("Soil temperature 1990–2010, LM4+ against ERA5-Land on its own four layers\n"
             "top: annual mean bias;  bottom: amplitude of the annual cycle, "
             "model divided by reference (below 1 = too damped)", fontsize=15)
fig.savefig("figures/soilT_vs_era5land.png", dpi=140, bbox_inches="tight")
print("\nwrote figures/soilT_vs_era5land.png")
