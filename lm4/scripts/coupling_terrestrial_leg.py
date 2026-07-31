"""Terrestrial leg of land-atmosphere coupling in LM4+ offline, MJJAS 1982-1996.

The chain is soil moisture -> surface fluxes -> boundary layer -> precipitation.
Only the first link can be measured offline, because the prescribed atmosphere
cannot respond -- which is precisely what makes the measurement clean here:
causality runs one way, with none of the feedback contamination a coupled run
carries.  The atmospheric leg belongs to the coupled/AMIP runs (project variable
plan, T3-7).

From daily anomalies about each year's MJJAS mean:
  rho     correlation of root-zone soil moisture with evapotranspiration
  slope   dET/dSM
  I_TCI   sigma(SM) x dET/dSM   -- Dirmeyer's terrestrial coupling index, i.e.
          how much ET actually moves given how much the soil actually varies

A strong terrestrial leg needs both sensitivity and variability; either alone is
not coupling.  Coupling is expected to peak in transitional climates, weak where
evaporation is energy-limited (wet) and weak again where there is no water to
vary (desert).

Input : lm4/data/coupling_daily_1982_1996.npz
Output: figures/coupling_terrestrial_leg.png, lm4/data/coupling_leg_regions.csv
"""
import sys
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

sys.path.insert(0, "lm4/scripts")
from greenland_mask import in_greenland

LV = 2.5e6            # latent heat of vaporisation, J/kg
z = np.load("lm4/data/coupling_daily_1982_1996.npz")
lat = z["lat"]
lon = np.where(z["lon"] > 180, z["lon"] - 360, z["lon"])
keep = z["soil"] & ~in_greenland(lat, lon)
n, sxx, syy, sxy = z["n"], z["sxx"], z["syy"], z["sxy"]

with np.errstate(invalid="ignore", divide="ignore"):
    rho = sxy / np.sqrt(sxx * syy)
    slope = sxy / sxx                       # d ET / d SM,  kg/(m2 s) per m3/m3
    sd_sm = np.sqrt(sxx / (n - 1))
tci = sd_sm * slope * LV                    # W/m2 -- ET expressed as latent heat
rho = np.where(keep & (n > 100), rho, np.nan)
tci = np.where(keep & (n > 100), tci, np.nan)
sd_sm = np.where(keep & (n > 100), sd_sm, np.nan)

NLAT, NLON = 180, 360
lat1 = 89.5 - np.arange(NLAT)
lon1 = -179.5 + np.arange(NLON)
ilat = np.clip(((90.0 - lat) / 1.0).astype(int), 0, NLAT - 1)
ilon = np.clip(((lon + 180.0) / 1.0).astype(int), 0, NLON - 1)


def grid(v):
    s = np.zeros((NLAT, NLON))
    c = np.zeros((NLAT, NLON))
    ok = np.isfinite(v)
    np.add.at(s, (ilat[ok], ilon[ok]), v[ok])
    np.add.at(c, (ilat[ok], ilon[ok]), 1.0)
    out = np.full((NLAT, NLON), np.nan)
    m = c > 0
    out[m] = s[m] / c[m]
    return out


G = {k: grid(v) for k, v in (("rho", rho), ("tci", tci), ("sd", sd_sm))}
common = np.isfinite(G["rho"])
W = np.cos(np.deg2rad(lat1))[:, None] * np.ones((1, NLON))
w = np.where(common, W, 0.0)


def am(x, s=common):
    ww = np.where(s, W, 0.0)
    return np.nansum(np.where(s, x, 0) * ww) / ww.sum()


print("terrestrial leg, MJJAS daily anomalies, %d cells" % common.sum())
print("  rho(SM,ET)   mean %.3f   median %.3f   cells rho>0.5 %.1f %%"
      % (am(G["rho"]), np.nanmedian(G["rho"][common]),
         100 * np.nanmean(G["rho"][common] > 0.5)))
print("  I_TCI        mean %.2f W/m2   p90 %.2f"
      % (am(G["tci"]), np.nanpercentile(G["tci"][common], 90)))

REG = [("Global", None), ("Amazon", (-10, 5, -70, -50)), ("Congo", (-5, 5, 12, 30)),
       ("SE Asia", (-10, 10, 95, 140)), ("Australia", (-35, -15, 115, 150)),
       ("Siberia", (55, 70, 60, 140)), ("East Asia", (20, 50, 100, 145)),
       ("North America", (30, 55, -125, -70))]
rows = []
print("\n  region            cells    rho    I_TCI [W/m2]   sd(SM)")
for name, bx in REG:
    s = common if bx is None else (common & (lat1[:, None] >= bx[0])
                                   & (lat1[:, None] < bx[1])
                                   & (lon1[None, :] >= bx[2])
                                   & (lon1[None, :] < bx[3]))
    if s.sum():
        print("  %-16s %5d   %+.3f    %8.2f     %.4f"
              % (name, s.sum(), am(G["rho"], s), am(G["tci"], s), am(G["sd"], s)))
        rows.append([s.sum(), am(G["rho"], s), am(G["tci"], s), am(G["sd"], s)])
np.savetxt("lm4/data/coupling_leg_regions.csv", np.array(rows), delimiter=",",
           header="ncells,rho,I_TCI_Wm2,sd_sm", comments="", fmt="%.5f")

proj = ccrs.PlateCarree()
fig, axes = plt.subplots(3, 1, figsize=(15, 15), subplot_kw={"projection": proj},
                         constrained_layout=True)
PAN = [("(a) correlation  ρ(SM, ET),  daily MJJAS anomalies", G["rho"],
        np.array([-.6, -.4, -.2, 0, .2, .4, .6, .8, 1.0]), "RdYlGn"),
       ("(b) terrestrial coupling index  σ(SM) × ∂LE/∂SM   [W/m²]", G["tci"],
        np.array([0, 1, 2, 4, 6, 9, 13, 18, 25]), "YlOrRd"),
       ("(c) daily soil-moisture variability  σ(SM)   [m³/m³]", G["sd"],
        np.array([0, .002, .004, .007, .01, .015, .02, .03, .045]), "YlGnBu")]
for ax, (name, fld, lv, cmap) in zip(axes, PAN):
    ax.set_extent([-180, 180, -58, 84], crs=proj)
    ax.add_feature(cfeature.COASTLINE, lw=0.45)
    im = ax.contourf(lon1, lat1, np.where(common, fld, np.nan), levels=lv,
                     cmap=cmap, extend="both", transform=proj)
    ax.set_title(name, fontsize=15, loc="left")
    gl = ax.gridlines(draw_labels=True, lw=0.3, alpha=0.4)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {"size": 10}
    gl.ylabel_style = {"size": 10}
    cb = fig.colorbar(im, ax=ax, orientation="vertical", pad=0.02, shrink=0.85,
                      ticks=lv)
    cb.ax.tick_params(labelsize=10)
fig.suptitle("Terrestrial leg of land–atmosphere coupling — LM4+ offline (WFDE5), "
             "MJJAS 1982–1996\nthe atmospheric leg needs the coupled run; offline "
             "measures this leg without feedback contamination", fontsize=16)
fig.savefig("figures/coupling_terrestrial_leg.png", dpi=140, bbox_inches="tight")
print("\nwrote figures/coupling_terrestrial_leg.png")
