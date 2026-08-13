"""Annual runoff, LM4+ vs G-RUN, by latitude band.

Three changes from runoff_vs_grun.py, which scored an MJJAS map:

  * both `runf` and `mrro`, because which one G-RUN should be compared against
    is not settled and the answer moves the headline from -13 % to -39 %.
    The earlier note picked mrro on the grounds that runf carries the solid part
    and the glacier and lake tiles.  The numbers do not support that reading:
    frunf is 0.34 % of runf, soil_area/land_area has a median of 0.997, and mrro
    is still 22 % below runf in cells that are pure soil with no frozen runoff
    at all (the Amazon: 688 vs 906 mm/yr).  The source says why --
        land_model.F90:2550  runf = snow_lrunf + snow_frunf + subs_lrunf
        soil.F90:2996        mrro = lrunf_ie + lrunf_sn + lrunf_bf + lrunf_nu
    runf is sent from every tile; mrro is sent from inside the soil module only,
    so meltwater running off the snowpack without entering the soil column is in
    runf and not in mrro.  Gauge streamflow contains it.  On that reading runf is
    the counterpart, but the components are not traced end to end here, so both
    are reported and neither is presented as the answer.
  * annual, not MJJAS.  How much water leaves the land in a year is the
    quantity that matters for the ocean, and at high latitude a summer mean is
    dominated by one snowmelt pulse.
  * scored by latitude band, because the high latitudes are where the freshwater
    question lives and a global number hides them.

Only years with all twelve months are used -- 1990 and 1997-2010.  1991-1996
stop at November (NOTES 13.31), and an annual total missing December is not an
annual total.

Caveat to carry with the high-latitude scores: G-RUN is a machine-learning
reconstruction trained on gauged catchments, and Arctic gauge density is low, so
above 60N it is closer to an extrapolation than to an observation.  Disagreement
there is weaker evidence against the model than it looks.

Inputs : lm4/data/runoff_monthly_1990_2010.npz, G-RUN ensemble mean
Output : figures/runoff_vs_grun_annual.png, lm4/data/runoff_grun_bands.csv
"""
import sys
import numpy as np
import netCDF4 as nc
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

sys.path.insert(0, "lm4/scripts")
from greenland_mask import in_greenland

GRUN = "/Users/youngdaekoh/data2/runoff/GRUN/G-RUN_ENSEMBLE_MMM.nc"
NPZ = "lm4/data/runoff_monthly_1990_2010.npz"
YEARS = np.array([1990] + list(range(1997, 2011)))   # twelve-month years only
NLAT, NLON = 180, 360
lat1 = 89.5 - np.arange(NLAT)
lon1 = -179.5 + np.arange(NLON)
S = 86400.0 * 365.0                                   # kg/m2/s -> mm/yr
BANDS = [(60, 90, "60-90N"), (50, 60, "50-60N"), (30, 50, "30-50N"),
         (0, 30, "0-30N"), (-30, 0, "0-30S"), (-60, -30, "30-60S")]

# ------------------------------------------------------------------ G-RUN ---
d = nc.Dataset(GRUN)
gy = np.array(d.variables["Y"][:], "f8")
gx = np.array(d.variables["X"][:], "f8")
units = getattr(d.variables["Runoff"], "units", "?")
tv = d.variables["time"]
dates = nc.num2date(tv[:], tv.units, only_use_cftime_datetimes=False)
print("G-RUN: %s, Y %.2f..%.2f  X %.2f..%.2f" % (units, gy[0], gy[-1], gx[0], gx[-1]))

gr = np.full((YEARS.size, NLAT, NLON), np.nan)
for iy, y in enumerate(YEARS):
    k = [i for i, t in enumerate(dates) if t.year == y]
    if len(k) != 12:
        raise SystemExit("G-RUN has %d months in %d" % (len(k), y))
    a = np.nanmean(np.stack([np.ma.filled(d.variables["Runoff"][i].astype("f8"), np.nan)
                             for i in k]), axis=0)     # mm/day, annual mean
    if gy[0] < gy[-1]:
        a = a[::-1]                                    # to descending latitude
    b = a.reshape(NLAT, 2, NLON, 2)
    with np.errstate(invalid="ignore"):
        gr[iy] = np.nanmean(b, axis=(1, 3))
d.close()
if gx.max() > 180:
    gr = np.roll(gr, NLON // 2, axis=2)
gr = gr * 365.0                                        # mm/day -> mm/yr
print("G-RUN annual mean over valid cells: %.1f mm/yr" % np.nanmean(gr))

# ------------------------------------------------------------------- LM4 ----
z = np.load(NPZ)
mlat = z["lat"]
mlon = np.where(z["lon"] > 180, z["lon"] - 360, z["lon"])
soil = z["soil"]
keep = soil & ~in_greenland(mlat, mlon)
ilat = np.clip(((90.0 - mlat) / 1.0).astype(int), 0, NLAT - 1)
ilon = np.clip(((mlon + 180.0) / 1.0).astype(int), 0, NLON - 1)
yr_all = z["years"]
iy_keep = np.array([np.where(yr_all == y)[0][0] for y in YEARS])
DEFS = {"runf": np.nanmean(z["runf"][iy_keep], axis=1) * S,
        "mrro": np.nanmean(z["mrro"][iy_keep], axis=1) * S}   # (year, point) mm/yr


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


lm = np.stack([bin_points(mrro_ann[i]) for i in range(YEARS.size)])
mm, gg = np.nanmean(lm, axis=0), np.nanmean(gr, axis=0)
common = np.isfinite(mm) & np.isfinite(gg)
W = np.cos(np.deg2rad(lat1))[:, None] * np.ones((1, NLON))
print("common cells: %d" % common.sum())

rows = []
print("\n%-8s %7s %9s %9s %9s %8s %7s" %
      ("band", "cells", "LM4", "G-RUN", "bias", "bias%", "r"))
for a0, a1, name in [(-90, 90, "global")] + BANDS:
    s = common & (lat1[:, None] >= a0) & (lat1[:, None] < a1)
    if s.sum() < 20:
        continue
    w = np.where(s, W, 0.0)
    m_ = np.nansum(np.where(s, mm, 0) * w) / w.sum()
    g_ = np.nansum(np.where(s, gg, 0) * w) / w.sum()
    r = np.corrcoef(mm[s], gg[s])[0, 1]
    print("%-8s %7d %9.1f %9.1f %+9.1f %+7.1f%% %7.3f"
          % (name, s.sum(), m_, g_, m_ - g_, 100 * (m_ - g_) / g_, r))
    rows.append([a0, a1, s.sum(), m_, g_, m_ - g_, r])

np.savetxt("lm4/data/runoff_grun_bands.csv", np.array(rows), delimiter=",",
           header="lat0,lat1,ncells,lm4_mmyr,grun_mmyr,bias_mmyr,r",
           comments="", fmt="%.4f")

# --------------------------------------------------------------- figure -----
proj = ccrs.PlateCarree()
fig, axes = plt.subplots(1, 3, figsize=(19, 4.8), subplot_kw={"projection": proj},
                         constrained_layout=True)
LV = np.array([0, 25, 50, 100, 150, 250, 400, 600, 900, 1400])
LVD = np.array([-400, -250, -150, -80, -30, 30, 80, 150, 250, 400])
for ax, (fld, lv, cmap, ttl) in zip(axes, (
        (np.where(common, gg, np.nan), LV, "YlGnBu", "G-RUN (obs-based)"),
        (np.where(common, mm, np.nan), LV, "YlGnBu", "LM4+ mrro (model)"),
        (np.where(common, mm - gg, np.nan), LVD, "BrBG", "LM4+ − G-RUN"))):
    ax.set_extent([-180, 180, -58, 84], crs=proj)
    ax.add_feature(cfeature.COASTLINE, lw=0.4)
    im = ax.contourf(lon1, lat1, fld, levels=lv, cmap=cmap, extend="both",
                     transform=proj)
    ax.set_title(ttl, fontsize=14)
    ax.axhline(60, color="k", lw=0.8, ls="--")
    gl = ax.gridlines(draw_labels=True, lw=0.3, alpha=0.4)
    gl.top_labels = False
    gl.right_labels = False
    cb = fig.colorbar(im, ax=ax, orientation="horizontal", ticks=lv,
                      shrink=0.9, pad=0.02, aspect=30)
    cb.ax.tick_params(labelsize=9)
    cb.set_label("annual runoff [mm/yr]", fontsize=11)

fig.suptitle("Annual runoff %d–%d (twelve-month years only) — LM4+ `mrro` vs "
             "G-RUN ensemble mean, common 1° cells\n"
             "dashed line 60N: above it G-RUN is a reconstruction from sparse "
             "gauges, not an observation" % (YEARS.min(), YEARS.max()),
             fontsize=13)
fig.savefig("figures/runoff_vs_grun_annual.png", dpi=140, bbox_inches="tight")
print("\nwrote figures/runoff_vs_grun_annual.png")
