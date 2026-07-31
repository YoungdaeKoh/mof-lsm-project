"""Runoff, LM4+ vs G-RUN, MJJAS 1982-1996: global and East Asia.

G-RUN is a machine-learning reconstruction of gridded runoff trained on gauge
records, so it is an observational constraint but not a direct measurement --
and it was trained under its own meteorological forcing, which is not WFDE5.
Any bias therefore mixes model error with a forcing difference; the pattern and
the seasonal/interannual behaviour are the trustworthy part.

Grid runoff is not river discharge.  Freshwater reaching the Yellow Sea needs
the routed `river` stream, which is a separate calculation.

East Asia box follows the project's existing definition (20-50N, 100-145E,
analysis/diag/temp_timeseries_region.py).

Inputs : lm4/data/monthly_noice_16yr.csv is not enough (needs the field), so the
         model side is re-extracted per cell by extract_runoff_grid.py
Output : figures/runoff_vs_grun.png, lm4/data/runoff_vs_grun_scores.csv
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
NPZ = "lm4/data/runoff_1982_1996.npz"
YEARS = np.arange(1982, 1997)
MONTHS = (5, 6, 7, 8, 9)
NLAT, NLON = 180, 360
lat1 = 89.5 - np.arange(NLAT)
lon1 = -179.5 + np.arange(NLON)
EA = (20, 50, 100, 145)

# ------------------------------------------------------------------ G-RUN ---
d = nc.Dataset(GRUN)
gy = np.array(d.variables["Y"][:], "f8")
gx = np.array(d.variables["X"][:], "f8")
tv = d.variables["time"]
dates = nc.num2date(tv[:], tv.units, only_use_cftime_datetimes=False)
print("G-RUN grid: Y %d %.3f..%.3f   X %d %.3f..%.3f"
      % (gy.size, gy[0], gy[-1], gx.size, gx[0], gx[-1]))
print("  units of Runoff: %s" % getattr(d.variables["Runoff"], "units", "-"))

sel = {y: [i for i, t in enumerate(dates) if t.year == y and t.month in MONTHS]
       for y in YEARS}
gr = np.full((YEARS.size, NLAT, NLON), np.nan)
for iy, y in enumerate(YEARS):
    acc = None
    for k in sel[y]:
        a = np.ma.filled(d.variables["Runoff"][k].astype("f8"), np.nan)
        acc = a if acc is None else acc + a
    a = acc / len(sel[y])                       # 0.5 deg MJJAS mean
    if gy[0] > gy[-1]:                          # make lat descending -> keep
        pass
    else:
        a = a[::-1]
    b = a.reshape(NLAT, 2, NLON, 2)
    with np.errstate(invalid="ignore"):
        gr[iy] = np.nanmean(b, axis=(1, 3))
d.close()
if gx.max() > 180:
    gr = np.roll(gr, NLON // 2, axis=2)
print("G-RUN MJJAS mean: %.4f (native units)" % np.nanmean(gr))

# ------------------------------------------------------------------- LM4 ----
z = np.load(NPZ)
mlat, mlon = z["lat"], np.where(z["lon"] > 180, z["lon"] - 360, z["lon"])
keep = ~in_greenland(mlat, mlon)
ilat = np.clip(((90.0 - mlat) / 1.0).astype(int), 0, NLAT - 1)
ilon = np.clip(((mlon + 180.0) / 1.0).astype(int), 0, NLON - 1)


def bin_model(v):
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


ms = np.stack([bin_model(z["mod"][i]) for i in range(YEARS.size)]) * 86400.0
common = np.all(np.isfinite(ms), axis=0) & np.all(np.isfinite(gr), axis=0)
W = np.cos(np.deg2rad(lat1))[:, None] * np.ones((1, NLON))

mm, gg = ms.mean(axis=0), gr.mean(axis=0)
print("\nMJJAS runoff, %d common 1-deg cells" % common.sum())
scores = []
for name, sel_mask in (("global", common),
                       ("East Asia", common & (lat1[:, None] >= EA[0])
                        & (lat1[:, None] < EA[1]) & (lon1[None, :] >= EA[2])
                        & (lon1[None, :] < EA[3]))):
    w = np.where(sel_mask, W, 0.0)
    a = np.nansum(np.where(sel_mask, mm, 0) * w) / w.sum()
    b = np.nansum(np.where(sel_mask, gg, 0) * w) / w.sum()
    r = np.corrcoef(mm[sel_mask], gg[sel_mask])[0, 1]
    d_ = mm - gg
    rmse = np.sqrt(np.nansum(np.where(sel_mask, d_ ** 2, 0) * w) / w.sum())
    print("  %-10s n=%5d   LM4 %.4f   G-RUN %.4f   bias %+.4f (%+.1f %%)  "
          "RMSE %.4f  r %.3f"
          % (name, sel_mask.sum(), a, b, a - b, (a - b) / b * 100, rmse, r))
    scores.append([sel_mask.sum(), a, b, a - b, rmse, r])
np.savetxt("lm4/data/runoff_vs_grun_scores.csv", np.array(scores), delimiter=",",
           header="ncells,lm4,grun,bias,rmse,r  (rows: global, East Asia)",
           comments="", fmt="%.5f")

# ------------------------------------------------------------------ figure ---
LV = np.array([0, .1, .25, .5, .75, 1, 1.5, 2, 3, 5])
LVD = np.array([-2, -1.5, -1, -.5, -.25, .25, .5, 1, 1.5, 2])
proj = ccrs.PlateCarree()
fig, axes = plt.subplots(2, 3, figsize=(19, 9), subplot_kw={"projection": proj},
                         constrained_layout=True)
titles = ["G-RUN (reconstruction)", "LM4+ (model)", "LM4+ − G-RUN"]
for r, (name, ext) in enumerate((("global", [-180, 180, -58, 84]),
                                 ("East Asia", [EA[2] - 5, EA[3] + 5,
                                                EA[0] - 5, EA[1] + 5]))):
    ims = []
    for c, (fld, lv, cmap) in enumerate(((gg, LV, "YlGnBu"), (mm, LV, "YlGnBu"),
                                         (mm - gg, LVD, "BrBG"))):
        ax = axes[r, c]
        ax.set_extent(ext, crs=proj)
        ax.add_feature(cfeature.COASTLINE, lw=0.5)
        if r == 1:
            ax.add_feature(cfeature.BORDERS, lw=0.35, ls=":")
        ims.append(ax.contourf(lon1, lat1, np.where(common, fld, np.nan),
                               levels=lv, cmap=cmap,
                               extend="max" if c < 2 else "both", transform=proj))
        ax.set_title("%s   %s" % (titles[c], name), fontsize=14)
        gl = ax.gridlines(draw_labels=True, lw=0.3, alpha=0.4)
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {"size": 10}
        gl.ylabel_style = {"size": 10}
    cb = fig.colorbar(ims[0], ax=[axes[r, 0], axes[r, 1]], orientation="horizontal",
                      ticks=lv, shrink=0.7, pad=0.02, aspect=45)
    cb.ax.tick_params(labelsize=10)
    cb.set_label("MJJAS runoff [mm/day]", fontsize=12)
    cb2 = fig.colorbar(ims[2], ax=axes[r, 2], orientation="horizontal",
                       ticks=LVD, shrink=0.9, pad=0.02, aspect=25)
    cb2.ax.tick_params(labelsize=10)
    cb2.set_label("difference [mm/day]", fontsize=12)

fig.suptitle("MJJAS runoff 1982–1996 — LM4+ offline (WFDE5) vs G-RUN, common 1° cells\n"
             "top: global,  bottom: East Asia (20–50°N, 100–145°E).  "
             "G-RUN is a gauge-trained reconstruction under its own forcing, "
             "so read the pattern rather than the absolute bias", fontsize=15)
fig.savefig("figures/runoff_vs_grun.png", dpi=140, bbox_inches="tight")
print("\nwrote figures/runoff_vs_grun.png")
