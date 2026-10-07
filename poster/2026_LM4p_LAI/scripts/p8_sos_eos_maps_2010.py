#!/usr/bin/env python3
"""Maps of SOS/EOS in 2010: where do the pilot runs move the dates, and by how many days?

Per 1-deg cell (north of 20N, seasonal amplitude >= 0.5 in GIMMS), monthly 2010 LAI is interpolated
to days and SOS/EOS are the 50 % amplitude crossings (same definition as Fig. 2).  Runs come from
../data/<run>.lai.2010-2010.1deg.nc, observations from GIMMS 2010.
output: ../figures/fig4_sos_eos_maps_2010.png, ../data/sos_eos_maps_2010.npz, ../data/sos_eos_maps_2010.txt
Map rows: EOS and SOS.  Columns: GIMMS date; CTRL - GIMMS; DL14+T10 - GIMMS; DL14+T10 - CTRL (shift the rule produced).
"""
import os
import numpy as np
import netCDF4 as nc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

YEAR = 2010
D = np.arange(1, 366.0)
MID = np.array([15.5, 45, 74.5, 105, 135.5, 166, 196.5, 227.5, 258, 288.5, 319, 349.5])
RUNS = [("base", "CTRL"), ("tc10", "TC10"), ("offon", "DL14+T10"), ("dayl", "DL13/12"), ("dayl2", "DLtype")]

g = nc.Dataset("../data/gimms_lai_mon_1982_2020.nc")
gname = [v for v in g.variables if g.variables[v].ndim == 3][0]
i0 = (YEAR - 1982) * 12
lat = np.asarray(g["lat"][:]); lon = np.asarray(g["lon"][:])
fields = {"GIMMS": np.ma.filled(g.variables[gname][i0:i0 + 12].astype("f8"), np.nan)}
for key, label in RUNS:
    f = "../data/%s.lai.%d-%d.1deg.nc" % (key, YEAR, YEAR)
    if os.path.exists(f):
        fields[label] = np.ma.filled(nc.Dataset(f).variables["lai"][:].astype("f8"), np.nan)
# all land south to 60S: EOS is meaningful in both hemispheres within a calendar year (SH peak Jan-Mar,
# decline Mar-May); SOS is only meaningful north of 20N and is reported there only
ok = (lat[:, None] > -60) & np.ones((1, lon.size), bool)
for v in fields.values():
    ok &= np.isfinite(v).all(0)
ok &= (fields["GIMMS"].max(0) - fields["GIMMS"].min(0)) >= 0.5


def dates(m):
    c = np.interp(D, np.r_[MID[-1] - 365, MID, MID[0] + 365], np.r_[m[-1], m, m[0]])
    thr = c.min() + 0.5 * (c.max() - c.min()); ip = int(c.argmax())
    up = [k for k in range(ip) if c[k] < thr <= c[k + 1]]
    dn = [k for k in range(ip, 364) if c[k] >= thr > c[k + 1]]
    s = D[up[-1]] + (thr - c[up[-1]]) / (c[up[-1] + 1] - c[up[-1]]) if up else np.nan
    e = D[dn[0]] + (c[dn[0]] - thr) / (c[dn[0]] - c[dn[0] + 1]) if dn else np.nan
    return s, e


sos = {k: np.full(ok.shape, np.nan) for k in fields}; eos = {k: np.full(ok.shape, np.nan) for k in fields}
for i, j in zip(*np.where(ok)):
    for k, v in fields.items():
        sos[k][i, j], eos[k][i, j] = dates(v[:, i, j])
np.savez("../data/sos_eos_maps_2010.npz", lat=lat, lon=lon, **{"sos_" + k: v for k, v in sos.items()}, **{"eos_" + k: v for k, v in eos.items()})

W = np.cos(np.radians(lat))[:, None] * np.ones((1, lon.size))
out = ["SOS/EOS %d per 1-deg cell (50 %% amplitude, monthly interpolated), differences in days, cos-lat weighted means; + = later than GIMMS" % YEAR, ""]
for band in ((20, 90), (50, 70), (40, 50), (20, 40), (-60, -20)):
    m = ok & (lat[:, None] >= band[0]) & (lat[:, None] < band[1])
    line = "%2d-%2dN (%5d cells)" % (*band, m.sum())
    for k in fields:
        if k == "GIMMS":
            continue
        de = eos[k] - eos["GIMMS"]; ds = sos[k] - sos["GIMMS"]; mm = m & np.isfinite(de) & np.isfinite(ds)
        line += " | %s: dEOS %+6.1f dSOS %+6.1f (EOS earlier than CTRL in %3.0f %% of cells)" % (
            k, np.nansum(de[mm] * W[mm]) / W[mm].sum(), np.nansum(ds[mm] * W[mm]) / W[mm].sum(),
            100 * np.mean((eos[k] - eos["CTRL"])[mm] < -1) if k != "CTRL" else 0)
    out.append(line)
open("../data/sos_eos_maps_2010.txt", "w").write("\n".join(out) + "\n"); print("\n".join(out))

rows = ["GIMMS", "CTRL \u2212 GIMMS", "DL14+T10 \u2212 GIMMS", "DL14+T10 \u2212 CTRL"]
proj = ccrs.PlateCarree(central_longitude=0)
fig, axs = plt.subplots(4, 2, figsize=(14.5, 7.6), subplot_kw={"projection": proj}, gridspec_kw={"hspace": 0.28, "wspace": 0.06})
date_ims, diff_ims = [], []
for c, (name, dd) in enumerate((("EOS", eos), ("SOS", sos))):
    panels = [dd["GIMMS"], dd["CTRL"] - dd["GIMMS"], dd["DL14+T10"] - dd["GIMMS"], dd["DL14+T10"] - dd["CTRL"]]
    for r, (title, z) in enumerate(zip(rows, panels)):
        ax = axs[r, c]
        if r == 0:
            im = ax.pcolormesh(lon, lat, np.ma.masked_invalid(z), cmap="viridis", vmin=200 if name == "EOS" else 90,
                               vmax=330 if name == "EOS" else 200, transform=ccrs.PlateCarree(), shading="auto")
            date_ims.append(im)
        else:
            im = ax.pcolormesh(lon, lat, np.ma.masked_invalid(z), cmap="RdBu_r", vmin=-60, vmax=60,
                               transform=ccrs.PlateCarree(), shading="auto")
            diff_ims.append(im)
        ax.coastlines(lw=0.4, color="0.3"); ax.add_feature(cfeature.BORDERS, lw=0.2, edgecolor="0.5")
        ax.set_extent([-180, 180, 20, 80], crs=ccrs.PlateCarree())
        ax.set_title("%s: %s" % (name, title), fontsize=10, loc="left")
        gl = ax.gridlines(draw_labels=True, lw=0.3, color="0.6", ls=":", xlocs=range(-180, 181, 60), ylocs=range(20, 81, 20))
        gl.top_labels = False; gl.right_labels = False; gl.xlabel_style = {"size": 7}; gl.ylabel_style = {"size": 7}
        if r < 3:
            gl.bottom_labels = False
for c, im in enumerate(date_ims):
    cb = fig.colorbar(im, ax=axs[0, c], orientation="vertical", pad=0.02, shrink=0.9); cb.set_label("Day of year", fontsize=8)
cb = fig.colorbar(diff_ims[0], ax=axs[1:, :].ravel().tolist(), orientation="vertical", pad=0.02, shrink=0.6)
cb.set_label("Days (+ = later than the reference)", fontsize=9)
fig.suptitle("Start (SOS) and end (EOS) of season %d, 50 %% amplitude of monthly LAI; red = later, blue = earlier" % YEAR, fontsize=11)
fig.savefig("../figures/fig4_sos_eos_maps_2010.png", dpi=170, bbox_inches="tight")

# ---- model C3-grass share on the 1-deg grid (area-weighted mean of the C96 cells in each box), from
#      phentest_species_frac_cells.py; panel (a) shows GIMMS only where c3grass holds >= GRASS_MIN of the July leaf area,
#      i.e. where the DL14+TC10 rule actually acts
GRASS_MIN = 0.5
sp = np.load("../data/base_species_share_july2010_c96.npz", allow_pickle=True)
k = list(sp["species"]).index("c3grass")
ci = np.clip(((sp["lat"] + 90) // 1).astype(int), 0, lat.size - 1); cj = np.clip(((sp["lon"] + 180) // 1).astype(int), 0, lon.size - 1)
good = np.isfinite(sp["share"][k]) & (sp["total_lai"] > 0.05)
num = np.zeros(ok.shape); den = np.zeros(ok.shape)
np.add.at(num, (ci[good], cj[good]), sp["share"][k][good] * sp["area"][good]); np.add.at(den, (ci[good], cj[good]), sp["area"][good])
grass = np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)
# 1-deg boxes that received no C96 cell (narrow boxes at high latitude) take the nearest cell's share
from scipy.spatial import cKDTree
tree = cKDTree(np.c_[sp["lat"][good], sp["lon"][good]])
gy, gx = np.meshgrid(lat, lon, indexing="ij")
empty = ok & ~np.isfinite(grass)
_, idx = tree.query(np.c_[gy[empty], gx[empty]])
grass[empty] = sp["share"][k][good][idx]
gmask_model = grass >= GRASS_MIN

# ---- observed grassland: MODIS MCD12C1 IGBP majority class (grid-verified, notes 13.70) aggregated to 1 deg;
#      a 1-deg cell counts as grassland when "Grassland" (class 10) is the most common of its 400 0.05-deg pixels (water excluded)
ig = nc.Dataset("/Volumes/data02/MODIS/MCD12C1/mcd12c1_igbp_GLOBAL_2010_2020.nc")
igbp = np.asarray(ig["igbp"][0]).reshape(180, 20, 360, 20).transpose(0, 2, 1, 3).reshape(180, 360, 400)
igbp_lat_ok = np.allclose(np.asarray(ig["lat"][:])[::20][:3], lat[:3] - 0.475, atol=0.05)   # both south-to-north
counts = np.apply_along_axis(lambda v: np.bincount(v[v > 0], minlength=17), 2, igbp)
mode = np.where(counts.sum(2) > 0, counts.argmax(2), 0)      # counts has shape (lat, lon, 17 classes)
gmask = mode == 10
assert igbp_lat_ok, "IGBP latitude order differs from the GIMMS grid"
m = ok & gmask & np.isfinite(eos["GIMMS"]) & np.isfinite(eos["CTRL"]) & np.isfinite(eos["DL14+T10"])
mm = ok & gmask_model & np.isfinite(eos["GIMMS"]) & np.isfinite(eos["CTRL"]) & np.isfinite(eos["DL14+T10"])
print("overlap: IGBP-grassland cells %d, model-C3-grass cells %d, both %d" % (m.sum(), mm.sum(), (m & mm).sum()))
print("IGBP grassland 1-deg cells (majority class): %d of %d seasonal cells | EOS CTRL-GIMMS %+.1f d, DL14+TC10-GIMMS %+.1f d, DL14+TC10-CTRL %+.1f d (cos-lat weighted)"
      % (m.sum(), ok.sum(), np.nansum((eos["CTRL"] - eos["GIMMS"])[m] * W[m]) / W[m].sum(),
         np.nansum((eos["DL14+T10"] - eos["GIMMS"])[m] * W[m]) / W[m].sum(), np.nansum((eos["DL14+T10"] - eos["CTRL"])[m] * W[m]) / W[m].sum()))

# ---- poster version: EOS only, three panels, global (60S-80N), with coordinate labels
fig, axs = plt.subplots(3, 1, figsize=(10, 11.5), subplot_kw={"projection": proj}, gridspec_kw={"hspace": 0.22})
panels = [("(a) EOS, GIMMS %d, grassland cells (MODIS IGBP majority class)" % YEAR,
           np.where(gmask, eos["GIMMS"], np.nan), "viridis", 60, 335, "Day of year"),
          ("(b) EOS, CTRL − GIMMS", eos["CTRL"] - eos["GIMMS"], "RdBu_r", -60, 60, "Days (+ = model later)"),
          ("(c) EOS, DL14+TC10 − CTRL", eos["DL14+T10"] - eos["CTRL"], "RdBu_r", -60, 60, "Days (+ = later than CTRL)")]
for ax, (title, z, cmap, lo, hi, lab) in zip(axs, panels):
    im = ax.pcolormesh(lon, lat, np.ma.masked_invalid(z), cmap=cmap, vmin=lo, vmax=hi, transform=ccrs.PlateCarree(), shading="auto")
    ax.coastlines(lw=0.4, color="0.3"); ax.add_feature(cfeature.BORDERS, lw=0.2, edgecolor="0.5")
    ax.set_extent([-180, 180, -60, 80], crs=ccrs.PlateCarree())
    ax.set_title(title, fontsize=11, loc="left")
    gl = ax.gridlines(draw_labels=True, lw=0.3, color="0.6", ls=":", xlocs=range(-180, 181, 60), ylocs=range(-60, 81, 30))
    gl.top_labels = False; gl.right_labels = False; gl.xlabel_style = {"size": 8}; gl.ylabel_style = {"size": 8}
    cb = fig.colorbar(im, ax=ax, orientation="vertical", pad=0.02, shrink=0.85); cb.set_label(lab, fontsize=8)
fig.suptitle("End of season %d (50 %% amplitude of monthly LAI); Southern Hemisphere EOS = its autumn (Mar–May)" % YEAR, fontsize=11)
fig.savefig("../figures/fig4b_eos_maps_2010.png", dpi=170, bbox_inches="tight")
