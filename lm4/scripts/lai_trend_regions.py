"""Is the drift global, or does it come from particular regions?

The global-mean version (lai_trend_vs_gimms.py) established that 1982-89 is
spin-up drift: the model rises 2.4x faster than GIMMS and then stops in 1990
while the observations keep greening.  A single global number cannot say whether
that is uniform, and the maps already showed it is not.

Boxes are picked from the bias and trend maps rather than from generic latitude
bands: the largest overestimate sits in the wet tropics, the worst band overall
is 60-30S (where the trend sign is wrong too), and the only underestimate is
boreal.  Same common 1-degree cells and cos(lat) weights as the global figure.

Two outputs so the boxes are defined once: a locator map carrying the letters,
and the time series panels carrying only those letters -- no coordinates repeated
on every panel.

Note MJJAS is the northern growing season; for Amazon, Congo and Australia it is
the dry season, so those panels are dry-season LAI.

Inputs : lm4/data/lm4_lai_1982_1996.npz, lm4/data/gimms_1deg_1982_1996.npz
Outputs: figures/lai_regions_map.png, figures/lai_trend_regions.png,
         lm4/data/lai_trend_regions.csv
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import MultipleLocator
import cartopy.crs as ccrs
import cartopy.feature as cfeature

YEARS = np.arange(1982, 1997)
NLAT, NLON = 180, 360
lat1 = 89.5 - np.arange(NLAT)
lon1 = -179.5 + np.arange(NLON)
LAT2 = lat1[:, None] * np.ones((1, NLON))
LON2 = np.ones((NLAT, 1)) * lon1[None, :]

# letter, name, (lat0, lat1, lon0, lon1);  None = whole common domain
REGIONS = [
    ("",  "Global land", None),
    ("A", "Amazon",    (-10, 5, -70, -50)),
    ("B", "Congo",     (-5, 5, 12, 30)),
    ("C", "SE Asia",   (-10, 10, 95, 140)),
    ("D", "Australia", (-35, -15, 115, 150)),
    ("E", "Siberia",   (55, 70, 60, 140)),
    # same East Asia box the CLM5 diagnostics use (analysis/diag/temp_timeseries_region.py)
    ("F", "East Asia", (20, 50, 100, 145)),
    ("G", "North America", (30, 55, -125, -70)),
]

z = np.load("lm4/data/lm4_lai_1982_1996.npz")
g = np.load("lm4/data/gimms_1deg_1982_1996.npz")
lat, lon, keep = z["lat"], z["lon"], z["keep"]
ilat = np.clip(((90.0 - lat) / 1.0).astype(int), 0, NLAT - 1)
ilon = np.clip(((lon + 180.0) / 1.0).astype(int), 0, NLON - 1)


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


ms = np.stack([bin_model(z["mjjas_%d" % y]) for y in YEARS])
gs = np.stack([g["mjjas_%d" % y] for y in YEARS])
common = np.all(np.isfinite(ms), axis=0) & np.all(np.isfinite(gs), axis=0)
W = np.cos(np.deg2rad(lat1))[:, None] * np.ones((1, NLON))


def mask_of(bx):
    if bx is None:
        return common
    la0, la1, lo0, lo1 = bx
    return common & (LAT2 >= la0) & (LAT2 < la1) & (LON2 >= lo0) & (LON2 < lo1)


def series(sel):
    w = np.where(sel, W, 0.0)
    a = np.array([np.nansum(np.where(sel, ms[i], 0) * w) / w.sum()
                  for i in range(len(YEARS))])
    b = np.array([np.nansum(np.where(sel, gs[i], 0) * w) / w.sum()
                  for i in range(len(YEARS))])
    return a, b, int(sel.sum())


def tr(v, s):
    return np.polyfit(YEARS[s], v[s], 1)[0] / abs(v[s].mean()) * 100


# ------------------------------------------------------------ locator map ----
proj = ccrs.PlateCarree()
fig = plt.figure(figsize=(14, 7))
ax = fig.add_subplot(1, 1, 1, projection=proj)
ax.set_extent([-180, 180, -58, 84], crs=proj)
ax.add_feature(cfeature.COASTLINE, lw=0.45)
bg = np.where(common, ms.mean(axis=0), np.nan)
im = ax.contourf(lon1, lat1, bg,
                 levels=[0, 0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0],
                 cmap="YlGn", extend="max", transform=proj)
for letter, name, bx in REGIONS:
    if bx is None:
        continue
    la0, la1, lo0, lo1 = bx
    ax.add_patch(Rectangle((lo0, la0), lo1 - lo0, la1 - la0, fill=False,
                           edgecolor="#1a1a1a", lw=2.0, transform=proj, zorder=5))
    ax.text(lo0 + (lo1 - lo0) / 2, la1 + 2.5, "%s  %s" % (letter, name),
            ha="center", va="bottom", fontsize=13, fontweight="bold",
            transform=proj, zorder=6,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#1a1a1a", lw=1.0))
gl = ax.gridlines(draw_labels=True, lw=0.3, alpha=0.4)
gl.top_labels = False
gl.right_labels = False
gl.xlabel_style = {"size": 11}
gl.ylabel_style = {"size": 11}
cb = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.06, shrink=0.6,
                  aspect=40)
cb.set_label("MJJAS mean LAI 1982–1996, LM4+ [m$^2$/m$^2$]", fontsize=12)
cb.ax.tick_params(labelsize=10)
ax.set_title("Regions used for the LAI time series", fontsize=15)
fig.tight_layout()
fig.savefig("figures/lai_regions_map.png", dpi=150)
print("wrote figures/lai_regions_map.png")

# ------------------------------------------------------------- time series ---
d1, d2 = YEARS <= 1989, YEARS >= 1990
rows = []
print("\nMJJAS LAI, common 1-deg cells, cos(lat) weighted")
print("%-16s %6s | %8s %8s | %8s %8s | %6s"
      % ("region", "cells", "LM4 82-89", "obs", "LM4 90-96", "obs", "bias"))
fig, axes = plt.subplots(2, 4, figsize=(25, 9))
for ax, (letter, name, bx) in zip(axes.ravel(), REGIONS):
    a, b, n = series(mask_of(bx))
    bias = a.mean() - b.mean()
    print("%-16s %6d | %+8.2f %+8.2f | %+8.2f %+8.2f | %+6.2f"
          % (name, n, tr(a, d1), tr(b, d1), tr(a, d2), tr(b, d2), bias))
    rows.append([n, tr(a, d1), tr(b, d1), tr(a, d2), tr(b, d2), bias])

    ax.plot(YEARS, a, "o-", color="#08519c", lw=2.2, ms=6, label="LM4+ (model)")
    ax.plot(YEARS, b, "s-", color="#238b45", lw=2.2, ms=6, label="GIMMS LAI4g")
    ax.set_title("%s %s" % (("(%s)" % letter) if letter else "", name),
                 fontsize=17, loc="left")
    ax.set_ylabel("LAI [m$^2$/m$^2$]", fontsize=14)
    ax.set_xlabel("year", fontsize=14)
    ax.tick_params(labelsize=13)
    ax.xaxis.set_major_locator(MultipleLocator(5))
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.grid(alpha=0.3, lw=0.5)
for k in range(len(REGIONS), axes.size):        # 7 regions, 8 slots
    axes.ravel()[k].axis("off")
axes[0, 0].legend(fontsize=13, loc="center right")
fig.suptitle("LAI by region — LM4+ vs GIMMS LAI4g, MJJAS mean on common 1° cells "
             "(boxes: see the locator map)", fontsize=16)
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig("figures/lai_trend_regions.png", dpi=140)

np.savetxt("lm4/data/lai_trend_regions.csv", np.array(rows), delimiter=",",
           header="ncells,lm4_8289,gimms_8289,lm4_9096,gimms_9096,bias",
           comments="", fmt="%.4f")
print("\nwrote figures/lai_trend_regions.png")
