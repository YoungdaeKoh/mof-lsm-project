"""Report figure: three diagnostic axes in one 3x3 panel.

The year-one criterion for the third checkpoint is "present model-observation
comparison results", and the cleanest way to satisfy it is one figure that shows
every axis in the same layout: reference, model, difference.

  row 1  vegetation      LAI, MJJAS            vs GIMMS LAI4g       (satellite)
  row 2  soil temperature root zone 0-100 cm   vs ERA5-Land         (model-based)
  row 3  runoff          annual total, mrro    vs G-RUN ENSEMBLE    (gauge-based)

Window 1990-2010 throughout: 1982-89 is spin-up drift, and including it makes the
model look like it agrees with the observed trend when it does not (NOTES 13.46).
Runoff uses only the fifteen years carrying all twelve months, since an annual
total missing December is not one.

Runoff is shown as mrro, the CMIP variable. Which model variable G-RUN should be
compared against is not settled -- runf gives a global bias of -13 % against
mrro's -39 % -- so the difference panel in row 3 is definition-dependent while
the spatial pattern is not. The text carries that caveat.

Inputs : lm4/data/{lm4_lai_1982_2010,gimms_1deg_1982_2010,
                   soilT_clim_1deg,runoff_monthly_1990_2010}.npz
         G-RUN ENSEMBLE
Output : figures/report_3axis_comparison.png
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import netCDF4 as nc
import cartopy.crs as ccrs
import cartopy.feature as cfeature

sys.path.insert(0, "lm4/scripts")
from greenland_mask import in_greenland

GRUN = "/Users/youngdaekoh/data2/runoff/GRUN/G-RUN_ENSEMBLE_MMM.nc"
NLAT, NLON = 180, 360
lat1 = 89.5 - np.arange(NLAT)
lon1 = -179.5 + np.arange(NLON)
YRS_LAI = np.arange(1982, 2011)
YRS_RUN = np.arange(1997, 2011)      # the run of consecutive twelve-month years
S_RUN = 86400.0 * 365.0                                 # kg/m2/s -> mm/yr


def binner(mlat, mlon, keep):
    ilat = np.clip(((90.0 - mlat) / 1.0).astype(int), 0, NLAT - 1)
    ilon = np.clip(((mlon + 180.0) / 1.0).astype(int), 0, NLON - 1)

    def go(v):
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
    return go


# ------------------------------------------------------------------- LAI ----
z = np.load("lm4/data/lm4_lai_1982_2010.npz")
g = np.load("lm4/data/gimms_1deg_1982_2010.npz")
bin_lai = binner(z["lat"], np.where(z["lon"] > 180, z["lon"] - 360, z["lon"]),
                 z["keep"])
lai_m = np.nanmean(np.stack([bin_lai(z["mjjas_%d" % y]) for y in YRS_LAI]), axis=0)
lai_o = np.nanmean(np.stack([g["mjjas_%d" % y] for y in YRS_LAI]), axis=0)

# ------------------------------------------------------- soil temperature ---
c = np.load("lm4/data/soilT_clim_1deg.npz")
WL = np.array([0.07, 0.21, 0.72])            # 0-7, 7-28, 28-100 cm
# annual, not MJJAS: a summer window compares the northern hemisphere in
# summer against the southern in winter, and the report's statement that the
# bias is uniform across all four layers only holds for the annual mean
st_m = np.einsum("l,lmyx->yx", WL, c["lm4"][:3].astype("f8")) / 12.0
st_o = np.einsum("l,lmyx->yx", WL, c["era5"][:3].astype("f8")) / 12.0

# ---------------------------------------------------------------- runoff ----
r = np.load("lm4/data/runoff_monthly_1990_2010.npz")
mlat = r["lat"]
mlon = np.where(r["lon"] > 180, r["lon"] - 360, r["lon"])
bin_run = binner(mlat, mlon, r["soil"] & ~in_greenland(mlat, mlon))
iy = np.array([np.where(r["years"] == y)[0][0] for y in YRS_RUN])
run_pts = np.nanmean(r["mrro"][iy], axis=1) * S_RUN          # (year, point)
run_m = np.nanmean(np.stack([bin_run(run_pts[i]) for i in range(YRS_RUN.size)]),
                   axis=0)

d = nc.Dataset(GRUN)
gy = np.array(d.variables["Y"][:], "f8")
gx = np.array(d.variables["X"][:], "f8")
dates = nc.num2date(d.variables["time"][:], d.variables["time"].units,
                    only_use_cftime_datetimes=False)
acc = []
for y in YRS_RUN:
    k = [i for i, t in enumerate(dates) if t.year == y]
    a = np.nanmean(np.stack([np.ma.filled(d.variables["Runoff"][i].astype("f8"),
                                          np.nan) for i in k]), axis=0)
    if gy[0] < gy[-1]:
        a = a[::-1]
    with np.errstate(invalid="ignore"):
        acc.append(np.nanmean(a.reshape(NLAT, 2, NLON, 2), axis=(1, 3)))
d.close()
run_o = np.nanmean(np.stack(acc), axis=0) * 365.0
if gx.max() > 180:
    run_o = np.roll(run_o, NLON // 2, axis=1)

# ------------------------------------------------------------------ rows ----
W = np.cos(np.deg2rad(lat1))[:, None] * np.ones((1, NLON))
ROWS = [
    ("LAI", "MJJAS 1982–2010", "m$^2$/m$^2$", lai_o, lai_m,
     "GIMMS LAI4g (obs)",
     np.array([0, 0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6]), "YlGn",
     np.array([-3, -2, -1.5, -1, -0.4, 0.4, 1, 1.5, 2, 3]), "RdBu_r"),
    ("Soil temperature", "annual 1982–2010", "K", st_o, st_m,
     "ERA5-Land (reference)",
     # annual root zone spans 260-307 K on the plotted cells (p1-p99)
     np.array([262, 270, 276, 281, 285, 289, 293, 297, 301, 306]), "RdYlBu_r",
     np.array([-6, -4, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 4, 6]), "RdBu_r"),
    ("Runoff", "annual 1997–2010", "mm/yr",
     run_o, run_m, "G-RUN (obs-based)",
     np.array([0, 25, 50, 100, 150, 250, 400, 600, 900, 1400]), "YlGnBu",
     np.array([-400, -250, -150, -80, -30, 30, 80, 150, 250, 400]), "BrBG"),
]

print("%-30s %7s %9s %9s %9s %7s"
      % ("axis", "cells", "reference", "model", "bias", "r"))
for name, period, unit, o, m, _, _, _, _, _ in ROWS:
    s = np.isfinite(o) & np.isfinite(m)
    w = np.where(s, W, 0.0)
    oo = np.nansum(np.where(s, o, 0) * w) / w.sum()
    mm = np.nansum(np.where(s, m, 0) * w) / w.sum()
    rr = np.corrcoef(o[s], m[s])[0, 1]
    print("%-30s %7d %9.2f %9.2f %+9.2f %7.3f"
          % (name, s.sum(), oo, mm, mm - oo, rr))

# ---------------------------------------------------------------- figure ----
proj = ccrs.PlateCarree()
# taller than the panels alone need: each row carries its own pair of horizontal
# colour bars underneath
fig, axes = plt.subplots(3, 3, figsize=(16.5, 11.4),
                         subplot_kw={"projection": proj}, constrained_layout=True)
fig.get_layout_engine().set(h_pad=0.012, hspace=0.012, w_pad=0.012, wspace=0.012)
LETTERS = "abcdefghi"

for i, (name, period, unit, o, m, oref, lv, cmap, lvd, cmapd) in enumerate(ROWS):
    s_ = np.isfinite(o) & np.isfinite(m)
    titles = ["%s — %s" % (name, oref),
              "%s — LM4+ (model)" % name,
              "%s — mean bias (model - obs)" % name]
    ims = []
    for j, (fld, levels, cm_, ext) in enumerate((
            (np.where(s_, o, np.nan), lv, cmap, "max"),
            (np.where(s_, m, np.nan), lv, cmap, "max"),
            (np.where(s_, m - o, np.nan), lvd, cmapd, "both"))):
        ax = axes[i, j]
        ax.set_extent([-180, 180, -58, 84], crs=proj)
        ax.add_feature(cfeature.COASTLINE, lw=0.35)
        ims.append(ax.contourf(lon1, lat1, fld, levels=levels, cmap=cm_,
                               extend=ext, transform=proj))
        ax.set_title("(%s) %s" % (LETTERS[i * 3 + j], titles[j]),
                     fontsize=14, loc="left", pad=4)
        # latitudes down the left column, longitudes along the bottom row only:
        # labelling all nine panels crowds a figure this dense
        gl = ax.gridlines(draw_labels=True, lw=0.25, alpha=0.35)
        gl.top_labels = gl.right_labels = False
        gl.left_labels = (j == 0)
        gl.bottom_labels = (i == 2)
        gl.xlabel_style = {"size": 11}
        gl.ylabel_style = {"size": 11}
    # the averaging window differs by row -- MJJAS for LAI, annual for the other
    # two, and runoff drops the years missing December -- so it is stated per row
    axes[i, 0].text(0.012, 0.055, period, transform=axes[i, 0].transAxes,
                    fontsize=9.5, va="bottom",
                    bbox=dict(fc="white", ec="0.6", lw=0.5, alpha=0.9, pad=2.0))
    # one bar centred under the reference/model pair, a second under the
    # difference: the two share no scale, so they must not share a bar
    # both bars the same physical length and thickness: the pair spans roughly
    # twice the width of a single panel, so its shrink is halved and the aspect
    # (length / thickness) is kept identical
    cb = fig.colorbar(ims[0], ax=[axes[i, 0], axes[i, 1]], orientation="horizontal",
                      location="bottom", ticks=lv, shrink=0.45, pad=0.02, aspect=22,
                      anchor=(0.5, 1.0), panchor=(0.5, 0.0))
    cb.ax.tick_params(labelsize=11)
    cb.set_label(unit, fontsize=12.5)
    cb2 = fig.colorbar(ims[2], ax=axes[i, 2], orientation="horizontal",
                       location="bottom", ticks=lvd, shrink=0.92, pad=0.02, aspect=22)
    cb2.ax.tick_params(labelsize=11)
    cb2.set_label(unit, fontsize=12.5)

fig.suptitle("LM4+ offline land simulation against reference datasets — "
             "common 1° grid, cos(lat) weighted", fontsize=17)
fig.savefig("figures/report_3axis_comparison.png", dpi=150, bbox_inches="tight")
print("\nwrote figures/report_3axis_comparison.png")
