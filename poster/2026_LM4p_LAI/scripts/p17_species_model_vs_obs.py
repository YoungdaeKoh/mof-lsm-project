#!/usr/bin/env python3
"""KMS poster: dominant LM4+ species (all six, trees and grasses) — observation-based map vs model.

(a) Observation-based: CLM5 surface dataset (MODIS-derived PFTs, Lawrence et al. 2019; simyr2000) mapped to the six LM4+
    species (lm4/data/replant/lm4_species_map_from_clm5.nc, replant_step1_crosswalk.py; crosswalk in notes 13.70)
(b) LM4+ 2010 (ctl state from the KIOST-ESM2 spin-up): species with the largest July leaf area per 1-deg cell
    (../data/model_species_dominance_1deg_2010.npz, p9_model_species_dominance_map.py)
Only cells vegetated in both maps are coloured. Shares north of 50N printed for the text.
(user request 2026-10-08: obs first, model second, include grasses -> six classes)
output: ../figures/fig_kms_species_model_vs_obs.png, ../data/kms_species_shares.txt
"""
import numpy as np
import netCDF4 as nc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import cartopy.crs as ccrs

SP = ["prioria", "picea", "larix", "acer", "c4grass", "c3grass"]          # LM4+ species order
LAB = ["Tropical evergreen tree (prioria)", "Evergreen needleleaf (picea)", "Deciduous needleleaf (larix)",
       "Deciduous broadleaf (acer)", "C4 grass", "C3 grass"]
COL = ["#756bb1", "#08519c", "#e31a1c", "#fd8d3c", "#e6c229", "#74c476"]

z = np.load("../data/model_species_dominance_1deg_2010.npz", allow_pickle=True)
lat, lon = z["lat"], z["lon"]; names = list(z["species"])
sh = np.nan_to_num(np.stack([z["share"][names.index(t)] for t in SP]).astype("f8"))   # July leaf-area share, (6, lat, lon)
mveg = sh.sum(0) > 0.05
mdom = np.where(mveg, sh.argmax(0), -1)

m = nc.Dataset("../../../lm4/data/replant/lm4_species_map_from_clm5.nc")
mlat = np.asarray(m["lat"][:]); mlon = np.asarray(m["lon"][:]) % 360
fr = np.nan_to_num(np.asarray(m["frac"][:], "f8"))                          # (6, lat, lon) % of natural vegetated area
ii = np.abs(mlat[:, None] - lat[None, :]).argmin(0); jj = np.abs(((mlon[:, None] - (lon[None, :] % 360) + 180) % 360) - 180).argmin(0)
of = fr[:, ii][:, :, jj]
oveg = of.sum(0) > 0
odom = np.where(oveg, of.argmax(0), -1)
both = mveg & oveg

N50 = both & (lat[:, None] >= 50)
w = np.cos(np.radians(lat))[:, None] * N50
out = ["Species shares north of 50N (cos-lat weighted, cells vegetated in both maps; %d cells)" % N50.sum(),
       "  obs = CLM5 PFT area share of natural vegetation (simyr2000); model = LM4+ July leaf-area share (2010)"]
for k, t in enumerate(SP):
    o = np.sum(of[k] / np.where(of.sum(0) > 0, of.sum(0), np.nan) * w, where=N50) / w.sum()
    mm = np.sum(sh[k] / np.where(sh.sum(0) > 0, sh.sum(0), np.nan) * w, where=N50) / w.sum()
    out.append("  %-8s obs %5.1f %%   model %5.1f %%   | dominant in %5d (obs) vs %5d (model) cells" % (
        t, 100 * o, 100 * mm, ((odom == k) & N50).sum(), ((mdom == k) & N50).sum()))
out.append("  same dominant species north of 50N: %.0f %%; globally: %.0f %% of %d cells" % (
    100 * np.mean((mdom == odom)[N50]), 100 * np.mean((mdom == odom)[both]), both.sum()))
open("../data/kms_species_shares.txt", "w").write("\n".join(out) + "\n"); print("\n".join(out))

cm = ListedColormap(COL); nm = BoundaryNorm(np.arange(-0.5, 6), cm.N)
proj = ccrs.PlateCarree()
fig, axs = plt.subplots(2, 1, figsize=(11, 7.2), subplot_kw={"projection": proj}, gridspec_kw={"hspace": 0.18})
for ax, d, t in ((axs[0], odom, "(a) Observation-based (MODIS-derived CLM5 PFT map)"), (axs[1], mdom, "(b) LM4+ (initial state from KIOST-ESM2)")):
    im = ax.pcolormesh(lon, lat, np.ma.masked_where(~both, d), cmap=cm, norm=nm, transform=proj, shading="auto")
    ax.coastlines(lw=0.4, color="0.3"); ax.set_extent([-180, 180, -55, 80], crs=proj); ax.set_title(t, loc="left", fontsize=12)
    gl = ax.gridlines(draw_labels=True, lw=0.3, color="0.6", ls=":", xlocs=range(-180, 181, 60), ylocs=range(-60, 81, 30))
    gl.top_labels = False; gl.right_labels = False
cb = fig.colorbar(im, ax=axs, orientation="vertical", pad=0.02, shrink=0.8, ticks=range(6)); cb.ax.set_yticklabels(LAB, fontsize=9)
fig.savefig("../figures/fig_kms_species_model_vs_obs.png", dpi=200, bbox_inches="tight")
print("wrote ../figures/fig_kms_species_model_vs_obs.png")
