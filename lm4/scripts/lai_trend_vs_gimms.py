"""Is the 1982-1989 rise in LM4 LAI spin-up drift or a real greening signal?

The run uses transient WFDE5 forcing, so a rising LAI could in principle be the
climate signal rather than initialisation adjustment.  GIMMS LAI4g settles it:
if the observations are flat over the same years and the same cells while the
model climbs, the rise is drift.

With the chain now finished to 2010 the comparison answers a second question the
sixteen-year version could not: over the twenty-one years after the drift ends,
does the model reproduce the observed greening rate, or only its sign?

Both fields are put on a common 1-degree grid and restricted to cells where both
are valid in every year, then averaged with cos(lat) weights.

GIMMS  : native 1/12 deg, semi-monthly, lat DESCENDING, lon -180..180
Model  : C96 land points binned into the same 1-degree boxes
Windows: Jan-Nov (the only window every archived year shares) and MJJAS

Output: lm4/data/lai_trend_vs_gimms.csv, figures/lai_trend_vs_gimms.png
"""
import glob
import numpy as np
import netCDF4 as nc
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

GIM = ("/Users/youngdaekoh/data2/LAI-DataKit/derived/gimms_lai4g/native0083/"
       "consolidated/GIMMS_LAI4g-consolidated_V1.2_%d%02d%02d.nc")
NPZ = "lm4/data/lm4_lai_1982_2010.npz"
YEARS = list(range(1982, 2011))
NLAT, NLON, R = 180, 360, 12          # 1 deg from 1/12 deg

lat1 = 89.5 - np.arange(NLAT)          # descending, matches GIMMS
lon1 = -179.5 + np.arange(NLON)

# --------------------------------------------------------------- GIMMS ------
def gimms_year(y, months):
    acc = np.zeros((NLAT, NLON))
    cnt = np.zeros((NLAT, NLON))
    for m in months:
        for half in (1, 2):
            f = GIM % (y, m, half)
            d = nc.Dataset(f)
            # netCDF4 applies scale_factor/add_offset itself -- do NOT redo it
            a = np.ma.filled(d.variables["lai"][0].astype("f8"), np.nan)
            d.close()
            a[a > 100] = np.nan
            a[a < 0] = np.nan
            b = a.reshape(NLAT, R, NLON, R)
            with np.errstate(invalid="ignore"):
                v = np.nanmean(b, axis=(1, 3))
            ok = np.isfinite(v)
            acc[ok] += v[ok]
            cnt[ok] += 1
    out = np.full((NLAT, NLON), np.nan)
    ok = cnt > 0
    out[ok] = acc[ok] / cnt[ok]
    return out

CACHE = "lm4/data/gimms_1deg_1982_2010.npz"
g_ann, g_mjj = {}, {}
try:
    c = np.load(CACHE)
    for y in YEARS:
        g_ann[y] = c["ann_%d" % y]
        g_mjj[y] = c["mjjas_%d" % y]
    print("loaded GIMMS 1-degree cache: %s" % CACHE)
except (FileNotFoundError, KeyError):
    print("reading GIMMS %d-%d (%d files) ..."
          % (YEARS[0], YEARS[-1], len(YEARS) * (11 + 5) * 2))
    for y in YEARS:
        g_ann[y] = gimms_year(y, range(1, 12))
        g_mjj[y] = gimms_year(y, range(5, 10))
        print("  %d  ann %.3f  mjjas %.3f  valid %d cells"
              % (y, np.nanmean(g_ann[y]), np.nanmean(g_mjj[y]),
                 np.isfinite(g_ann[y]).sum()))
    np.savez(CACHE, **{"ann_%d" % y: g_ann[y] for y in YEARS},
             **{"mjjas_%d" % y: g_mjj[y] for y in YEARS})
    print("cached to %s" % CACHE)

# --------------------------------------------------------------- model ------
z = np.load(NPZ)
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

m_ann = {y: bin_model(z["ann_%d" % y]) for y in YEARS}
m_mjj = {y: bin_model(z["mjjas_%d" % y]) for y in YEARS}

# ------------------------------------------------- common mask + means ------
W = np.cos(np.deg2rad(lat1))[:, None] * np.ones((1, NLON))

def series(gd, md):
    common = np.all([np.isfinite(gd[y]) & np.isfinite(md[y]) for y in YEARS], axis=0)
    w = np.where(common, W, 0.0)
    gs = np.array([np.nansum(np.where(common, gd[y], 0) * w) / w.sum() for y in YEARS])
    ms = np.array([np.nansum(np.where(common, md[y], 0) * w) / w.sum() for y in YEARS])
    return gs, ms, common

res = {}
for name, gd, md in (("Jan-Nov", g_ann, m_ann), ("MJJAS", g_mjj, m_mjj)):
    gs, ms, common = series(gd, md)
    res[name] = (gs, ms, common)
    yy = np.array(YEARS)
    print("\n=== %s  (common cells: %d) ===" % (name, common.sum()))
    print(" year   GIMMS    LM4")
    for i, Y in enumerate(YEARS):
        print("  %d  %6.3f  %6.3f" % (Y, gs[i], ms[i]))
    for lab, s in (("1982-1989", yy <= 1989), ("1990-2010", yy >= 1990),
                   ("1982-2010", yy > 0)):
        tg = np.polyfit(yy[s], gs[s], 1)[0]
        tm = np.polyfit(yy[s], ms[s], 1)[0]
        print("  %s trend  GIMMS %+.4f/yr (%+.2f %%/yr)   LM4 %+.4f/yr (%+.2f %%/yr)"
              % (lab, tg, tg / gs[s].mean() * 100, tm, tm / ms[s].mean() * 100))

np.savetxt("lm4/data/lai_trend_vs_gimms.csv",
           np.column_stack([YEARS, res["Jan-Nov"][0], res["Jan-Nov"][1],
                            res["MJJAS"][0], res["MJJAS"][1]]),
           delimiter=",", header="year,gimms_annov,lm4_annov,gimms_mjjas,lm4_mjjas",
           comments="", fmt="%.6f")

# --------------------------------------------------------------- figure -----
fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
yy = np.array(YEARS)
for ax, name in zip(axes, ("Jan-Nov", "MJJAS")):
    gs, ms, common = res[name]
    ax.plot(yy, ms, "o-", color="#08519c", lw=1.8, ms=4, label="LM4+ (model)")
    ax.plot(yy, gs, "s-", color="#238b45", lw=1.8, ms=4, label="GIMMS LAI4g (obs)")
    for s, ls in ((yy <= 1989, "--"), (yy >= 1990, "--")):
        for v, c in ((ms, "#08519c"), (gs, "#238b45")):
            p = np.polyfit(yy[s], v[s], 1)
            ax.plot(yy[s], np.polyval(p, yy[s]), ls, color=c, lw=1.0, alpha=0.8)
    def tr(v, s):
        return np.polyfit(yy[s], v[s], 1)[0] / v[s].mean() * 100
    d1, d2 = yy <= 1989, yy >= 1990
    ax.set_title("%-22s%10s%10s\n%-22s%+10.2f%+10.2f\n%-22s%+10.2f%+10.2f"
                 % ("%s  trend [%%/yr]" % name, "1982-89", "1990-2010",
                    "   LM4", tr(ms, d1), tr(ms, d2),
                    "   GIMMS", tr(gs, d1), tr(gs, d2)),
                 fontsize=9, loc="left", family="monospace")
    ax.set_xlabel("year")
    ax.set_ylabel("LAI [m$^2$/m$^2$]")
    ax.xaxis.set_major_locator(MultipleLocator(5))
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.grid(alpha=0.3, lw=0.5)
    ax.legend(fontsize=8.5)
fig.suptitle("Spin-up drift or real greening?  LM4+ vs GIMMS LAI4g on common 1° cells "
             "(%d cells, cos-lat weighted)" % res["Jan-Nov"][2].sum(), fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig("figures/lai_trend_vs_gimms.png", dpi=140)
print("\nwrote figures/lai_trend_vs_gimms.png")
