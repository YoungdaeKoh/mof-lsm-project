"""Surface soil moisture, LM4+ vs ESA CCI, MJJAS 1982-1996, northern hemisphere.

Scoped deliberately.  The coverage check (chk_cci_coverage.py) showed CCI has no
retrieval at all over the Amazon and Congo and only 25 % usable cells north of
60N, so it cannot speak to either region where our biases are largest.  What it
does cover well is 20-60N, which includes East Asia, so that is the domain here.

Absolute values are not compared.  CCI is a merged active/passive product with
known offsets in volumetric content, and it senses 0.5-5 cm against the model's
0-6 cm; the defensible metric is the interannual anomaly correlation, with the
mean and the coefficient of variation reported alongside as context rather than
as scores.

Inputs : lm4/data/sm_surface_1982_1996.npz, the CCI merged monthly file
Output : figures/sm_surface_vs_cci.png, lm4/data/sm_surface_vs_cci_scores.csv
"""
import sys
import numpy as np
import netCDF4 as nc
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

sys.path.insert(0, "lm4/scripts")
from greenland_mask import in_greenland

CCI = ("/Users/youngdaekoh/data2/SoilMoisture/ESACCI_SM_v9/"
       "ESACCI_SM_v202505_combined_monthly_197811-202412.nc")
YEARS = np.arange(1982, 1997)
MONTHS = (5, 6, 7, 8, 9)
NLAT, NLON = 180, 360
lat1 = 89.5 - np.arange(NLAT)
lon1 = -179.5 + np.arange(NLON)
LAT0, LAT1 = 20, 60                     # the band CCI actually covers
MINCOV = 0.8                            # >=4 of 5 MJJAS months per year

# --------------------------------------------------------------------- CCI --
d = nc.Dataset(CCI)
tv = d.variables["time"]
dates = nc.num2date(tv[:], tv.units, only_use_cftime_datetimes=False)
cci = np.full((YEARS.size, NLAT, NLON), np.nan)
cov = np.zeros((YEARS.size, NLAT, NLON))
for iy, y in enumerate(YEARS):
    ks = [i for i, t in enumerate(dates) if t.year == y and t.month in MONTHS]
    acc = np.zeros((720, 1440))
    cnt = np.zeros((720, 1440))
    for k in ks:
        a = np.ma.filled(d.variables["sm"][k].astype("f8"), np.nan)
        ok = np.isfinite(a)
        acc[ok] += a[ok]
        cnt[ok] += 1
    m = cnt > 0
    v = np.full((720, 1440), np.nan)
    v[m] = acc[m] / cnt[m]
    cci[iy] = np.nanmean(v.reshape(NLAT, 4, NLON, 4), axis=(1, 3))
    cov[iy] = (cnt / len(ks)).reshape(NLAT, 4, NLON, 4).mean(axis=(1, 3))
d.close()

# --------------------------------------------------------------------- LM4 --
z = np.load("lm4/data/sm_surface_1982_1996.npz")
mlat, mlon, soil = z["lat"], z["lon"], z["soil"]
mlon = np.where(mlon > 180, mlon - 360, mlon)
keep = soil & ~in_greenland(mlat, mlon)
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


ms = np.stack([bin_model(z["mod"][i]) for i in range(YEARS.size)])

band = (lat1[:, None] >= LAT0) & (lat1[:, None] < LAT1) * np.ones((1, NLON), bool)
common = (np.all(np.isfinite(ms), axis=0) & np.all(np.isfinite(cci), axis=0)
          & np.all(cov >= MINCOV, axis=0) & band)
print("usable cells in %d-%dN: %d" % (LAT0, LAT1, common.sum()))

W = np.cos(np.deg2rad(lat1))[:, None] * np.ones((1, NLON))
w = np.where(common, W, 0.0)


def am(x):
    return np.nansum(np.where(common, x, 0) * w) / w.sum()


mm, cm = ms.mean(axis=0), cci.mean(axis=0)
t = YEARS - YEARS.mean()
den = (t ** 2).sum()


def anom(a):
    an = a - a.mean(axis=0)
    sl = (an * t[:, None, None]).sum(axis=0) / den
    return an - sl[None] * t[:, None, None]      # detrended anomaly


am_, ac = anom(ms), anom(cci)
num = (am_ * ac).sum(axis=0)
dm = np.sqrt((am_ ** 2).sum(axis=0) * (ac ** 2).sum(axis=0))
with np.errstate(invalid="ignore", divide="ignore"):
    rho = np.where(dm > 0, num / dm, np.nan)

sdm, sdc = am_.std(axis=0, ddof=2), ac.std(axis=0, ddof=2)
with np.errstate(invalid="ignore", divide="ignore"):
    cvm, cvc = sdm / mm * 100, sdc / cm * 100

print("\nMJJAS surface soil moisture, %d-%dN, %d cells" % (LAT0, LAT1, common.sum()))
print("  mean            LM4 %.4f   CCI %.4f   (absolute offset is not a score)"
      % (am(mm), am(cm)))
print("  interannual sd  LM4 %.4f   CCI %.4f   ratio %.2f" % (am(sdm), am(sdc), am(sdm) / am(sdc)))
print("  CV [%%]          LM4 %.2f     CCI %.2f     ratio %.2f" % (am(cvm), am(cvc), am(cvm) / am(cvc)))
print("  anomaly correlation: area-weighted mean %.3f, median %.3f, "
      "cells with rho>0.5 %.1f %%"
      % (am(np.where(common, rho, np.nan)), np.nanmedian(rho[common]),
         100 * np.nanmean(rho[common] > 0.5)))
EA = common & (lon1[None, :] >= 100) & (lon1[None, :] < 145)
if EA.sum():
    wE = np.where(EA, W, 0.0)
    print("  East Asia (%d cells): anomaly r %.3f, CV ratio %.2f"
          % (EA.sum(), np.nansum(np.where(EA, rho, 0) * wE) / wE.sum(),
             (np.nansum(np.where(EA, cvm, 0) * wE) / wE.sum())
             / (np.nansum(np.where(EA, cvc, 0) * wE) / wE.sum())))

np.savetxt("lm4/data/sm_surface_vs_cci_scores.csv",
           np.array([[common.sum(), am(mm), am(cm), am(sdm), am(sdc),
                      am(np.where(common, rho, np.nan))]]),
           delimiter=",", header="ncells,lm4_mean,cci_mean,lm4_sd,cci_sd,anom_r",
           comments="", fmt="%.5f")

# ------------------------------------------------------------------ figure ---
proj = ccrs.PlateCarree()
fig, axes = plt.subplots(2, 2, figsize=(17, 8.5), subplot_kw={"projection": proj},
                         constrained_layout=True)
ext = [-180, 180, LAT0 - 3, LAT1 + 3]
PAN = [
    ("CCI mean", cm, np.array([0, .05, .1, .15, .2, .25, .3, .35, .4]), "YlGnBu"),
    ("LM4+ mean", mm, np.array([0, .05, .1, .15, .2, .25, .3, .35, .4]), "YlGnBu"),
    ("interannual sd, LM4 − CCI", sdm - sdc,
     np.array([-.04, -.03, -.02, -.01, -.003, .003, .01, .02, .03, .04]), "RdBu_r"),
    ("detrended anomaly correlation", rho,
     np.array([-.6, -.4, -.2, 0, .2, .4, .6, .8, 1.0]), "RdYlGn"),
]
for ax, (name, fld, lv, cmap) in zip(axes.ravel(), PAN):
    ax.set_extent(ext, crs=proj)
    ax.add_feature(cfeature.COASTLINE, lw=0.45)
    im = ax.contourf(lon1, lat1, np.where(common, fld, np.nan), levels=lv,
                     cmap=cmap, extend="both", transform=proj)
    ax.set_title(name, fontsize=14)
    gl = ax.gridlines(draw_labels=True, lw=0.3, alpha=0.4)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {"size": 9}
    gl.ylabel_style = {"size": 9}
    cb = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.03, shrink=0.8,
                      ticks=lv, aspect=35)
    cb.ax.tick_params(labelsize=9)
fig.suptitle("MJJAS surface (0–6 cm) soil moisture 1982–1996, %d–%d°N — "
             "LM4+ vs ESA CCI\nCCI cannot cover the Amazon, Congo or the boreal "
             "north; absolute offsets are not a score, the anomaly correlation is"
             % (LAT0, LAT1), fontsize=15)
fig.savefig("figures/sm_surface_vs_cci.png", dpi=140, bbox_inches="tight")
print("\nwrote figures/sm_surface_vs_cci.png")
