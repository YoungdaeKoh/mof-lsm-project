"""Root-zone (0-1 m) soil moisture, LM4+ vs ERA5-Land, MJJAS 1982-1996.

Three lenses in one figure, the same set used for LAI: mean state, interannual
variability (trend removed) and trend.  Depths match exactly -- LM4 layers 1-10
and ERA5 swvl1-3 both span 0 to 1 m -- and both fields are volumetric m3/m3, so
these are directly comparable numbers rather than proxies.

ERA5-Land is a reanalysis, not an observation: its soil moisture comes from
HTESSEL.  This is therefore a model intercomparison and should be labelled as
one, unlike the GIMMS LAI comparison.

Input : lm4/data/sm_rootzone_1982_1996.npz
Output: figures/sm_rootzone_vs_era5.png, lm4/data/sm_rootzone_scores.csv
"""
import sys
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

sys.path.insert(0, "lm4/scripts")
from greenland_mask import in_greenland

z = np.load("lm4/data/sm_rootzone_1982_1996.npz")
YEARS = z["years"]
lat1, lon1 = z["lat1"], z["lon1"]
NLAT, NLON = lat1.size, lon1.size
mlat = z["lat"]
mlon = np.where(z["lon"] > 180, z["lon"] - 360, z["lon"])
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


ms = np.stack([bin_model(z["mod"][i]) for i in range(len(YEARS))])
es = z["era"]
common = (np.all(np.isfinite(ms), axis=0) & np.all(np.isfinite(es), axis=0)
          & np.all(es > 0, axis=0))          # es is (year, lat, lon): reduce it too
W = np.cos(np.deg2rad(lat1))[:, None] * np.ones((1, NLON))

t = YEARS - YEARS.mean()
den = (t ** 2).sum()


def slope(a):
    an = a - a.mean(axis=0)
    return (an * t[:, None, None]).sum(axis=0) / den * 10.0


def sd_detrended(a):
    an = a - a.mean(axis=0)
    sl = (an * t[:, None, None]).sum(axis=0) / den
    return (an - sl[None] * t[:, None, None]).std(axis=0, ddof=2)


ROWS = [
    ("mean", "m$^3$/m$^3$", ms.mean(axis=0), es.mean(axis=0),
     np.array([0, .05, .1, .15, .2, .25, .3, .35, .4, .5]),
     np.array([-.15, -.1, -.06, -.03, -.01, .01, .03, .06, .1, .15])),
    ("interannual sd", "m$^3$/m$^3$", sd_detrended(ms), sd_detrended(es),
     np.array([0, .002, .004, .006, .01, .015, .02, .03, .04, .06]),
     np.array([-.03, -.02, -.012, -.006, -.002, .002, .006, .012, .02, .03])),
    ("trend", "m$^3$/m$^3$ per decade", slope(ms), slope(es),
     np.array([-.03, -.02, -.012, -.006, -.002, .002, .006, .012, .02, .03]),
     np.array([-.03, -.02, -.012, -.006, -.002, .002, .006, .012, .02, .03])),
]

scores = []
print("MJJAS root-zone (0-1 m) soil moisture, %d common 1-deg cells" % common.sum())
for name, unit, a, b, _, _ in ROWS:
    w = np.where(common, W, 0.0)
    am = np.nansum(np.where(common, a, 0) * w) / w.sum()
    bm = np.nansum(np.where(common, b, 0) * w) / w.sum()
    d = a - b
    rmse = np.sqrt(np.nansum(np.where(common, d ** 2, 0) * w) / w.sum())
    r = np.corrcoef(a[common], b[common])[0, 1]
    print("\n  %-16s LM4 %+.5f   ERA5 %+.5f   bias %+.5f (%+.1f %%)  RMSE %.5f  r %.3f"
          % (name, am, bm, am - bm, (am - bm) / abs(bm) * 100, rmse, r))
    print("    zonal   LM4      ERA5     bias")
    for a0, a1 in ((60, 85), (30, 60), (0, 30), (-30, 0), (-60, -30)):
        s = common & (lat1[:, None] >= a0) & (lat1[:, None] < a1)
        if s.sum():
            ww = np.where(s, W, 0.0)
            f = lambda x: np.nansum(np.where(s, x, 0) * ww) / ww.sum()
            print("    %4d..%-4d %8.4f %8.4f %+8.4f" % (a0, a1, f(a), f(b), f(a) - f(b)))
    scores.append([am, bm, am - bm, rmse, r])

np.savetxt("lm4/data/sm_rootzone_scores.csv", np.array(scores), delimiter=",",
           header="lm4,era5,bias,rmse,r  (rows: mean, sd, trend)", comments="", fmt="%.6f")

proj = ccrs.PlateCarree()
fig, axes = plt.subplots(3, 3, figsize=(19, 13), subplot_kw={"projection": proj},
                         constrained_layout=True)
titles = ["ERA5-Land (reanalysis)", "LM4+ (model)", "LM4+ − ERA5-Land"]
for r, (name, unit, a, b, lv, lvd) in enumerate(ROWS):
    cmap0 = "RdBu_r" if name == "trend" else ("YlOrRd" if name == "interannual sd" else "YlGnBu")
    ims = []
    for c, (fld, levels, cmap) in enumerate(((b, lv, cmap0), (a, lv, cmap0),
                                             (a - b, lvd, "RdBu_r"))):
        ax = axes[r, c]
        ax.set_extent([-180, 180, -58, 84], crs=proj)
        ax.add_feature(cfeature.COASTLINE, lw=0.4)
        ims.append(ax.contourf(lon1, lat1, np.where(common, fld, np.nan),
                               levels=levels, cmap=cmap,
                               extend="both" if name == "trend" else ("max" if c < 2 else "both"),
                               transform=proj))
        ax.set_title("%s   %s" % (titles[c], name), fontsize=14)
        gl = ax.gridlines(draw_labels=True, lw=0.3, alpha=0.4)
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {"size": 10}
        gl.ylabel_style = {"size": 10}
    cb = fig.colorbar(ims[0], ax=[axes[r, 0], axes[r, 1]], orientation="horizontal",
                      ticks=lv, shrink=0.7, pad=0.02, aspect=45)
    cb.ax.tick_params(labelsize=10)
    cb.set_label("%s [%s]" % (name, unit), fontsize=12)
    cb2 = fig.colorbar(ims[2], ax=axes[r, 2], orientation="horizontal",
                       ticks=lvd, shrink=0.9, pad=0.02, aspect=25)
    cb2.ax.tick_params(labelsize=10)
    cb2.set_label("difference [%s]" % unit, fontsize=12)

fig.suptitle("MJJAS root-zone (0–1 m) volumetric soil moisture 1982–1996 — "
             "LM4+ offline (WFDE5) vs ERA5-Land\n"
             "depths match exactly (LM4 layers 1–10, ERA5 swvl1–3);  "
             "ERA5-Land is a reanalysis, so this is a model intercomparison",
             fontsize=16)
fig.savefig("figures/sm_rootzone_vs_era5.png", dpi=140, bbox_inches="tight")
print("\nwrote figures/sm_rootzone_vs_era5.png")
