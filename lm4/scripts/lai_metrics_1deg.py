"""LAI: LM4 vs datakit GIMMS on a common 1-degree grid (JJA 1982-1986).

Method (common-grid upscaling):
  - GIMMS native 1/12 deg -> average the 12x12 pixels in each 1 deg box
    (reshape 2160x4320 -> 180x12x360x12, nanmean over the 12,12 axes).
  - LM4 C96 points -> bin each point into its 1 deg box, average.
  - Metrics (bias, RMSE, corr) over 1 deg LAND cells where BOTH have data.
Only compares where GIMMS is valid (deserts/ocean are NaN in GIMMS).
"""
import glob
import numpy as np
import netCDF4 as nc

YEARS = [1982, 1983, 1984, 1985, 1986]
GDIR = ("/Users/youngdaekoh/data2/LAI-DataKit/derived/gimms_lai4g/"
        "native0083/consolidated")

# ---- 1 deg common grid (cell centers) ----
lat1 = np.arange(-89.5, 90, 1.0)     # 180
lon1 = np.arange(-179.5, 180, 1.0)   # 360

# ---- GIMMS: aggregate JJA half-monthly files to 1 deg ----
gsum = np.zeros((180, 360))
gcnt = np.zeros((180, 360))
nfile = 0
for y in YEARS:
    for mm in ("06", "07", "08"):
        for f in sorted(glob.glob("%s/*_%d%s*.nc" % (GDIR, y, mm))):
            d = nc.Dataset(f)
            a = np.ma.filled(d.variables["lai"][0].astype("f8"), np.nan)  # (2160,4320)
            a[a > 100] = np.nan
            lat = d.variables["lat"][:]
            d.close()
            # native lat is descending; flip to ascending so box 0 = -90..-89
            a = a[::-1, :]
            # reshape to 1 deg boxes: 180x12 x 360x12
            box = a.reshape(180, 12, 360, 12)
            s = np.nansum(box, axis=(1, 3))
            c = np.sum(np.isfinite(box), axis=(1, 3))
            gsum += np.where(c > 0, s, 0)
            gcnt += c
            nfile += 1
gimms1 = np.where(gcnt > 0, gsum / np.where(gcnt > 0, gcnt, 1), np.nan)
print("GIMMS: %d half-month files aggregated; valid 1deg cells=%d"
      % (nfile, np.isfinite(gimms1).sum()))

# ---- LM4: 5-year JJA mean at C96 points -> bin to 1 deg ----
z = np.load("lm4_lai_jja_1982_1986.npz")
plat, plon = z["lat"], z["lon"]
lm4_pt = np.nanmean(np.stack([z["lai_%d" % y] for y in YEARS]), axis=0)
il = np.clip(((plat + 90)).astype(int), 0, 179)
jl = np.clip(((plon + 180)).astype(int), 0, 359)
lsum = np.zeros((180, 360)); lcnt = np.zeros((180, 360))
good = np.isfinite(lm4_pt)
np.add.at(lsum, (il[good], jl[good]), lm4_pt[good])
np.add.at(lcnt, (il[good], jl[good]), 1.0)
lm41 = np.where(lcnt > 0, lsum / np.where(lcnt > 0, lcnt, 1), np.nan)
print("LM4:   binned to 1deg; valid cells=%d" % np.isfinite(lm41).sum())

# ---- metrics where both valid ----
both = np.isfinite(gimms1) & np.isfinite(lm41)
n = both.sum()
lm4v, gv = lm41[both], gimms1[both]
bias = np.mean(lm4v - gv)
rmse = np.sqrt(np.mean((lm4v - gv) ** 2))
r = np.corrcoef(lm4v, gv)[0, 1]
print("\n=== LAI metrics (JJA 1982-1986, common 1deg, n=%d land cells) ===" % n)
print("LM4 mean   : %.3f" % lm4v.mean())
print("GIMMS mean : %.3f" % gv.mean())
print("bias (LM4-GIMMS): %+.3f" % bias)
print("RMSE            : %.3f" % rmse)
print("correlation     : %.3f" % r)

np.savez("lai_1deg_1982_1986.npz", lat=lat1, lon=lon1, lm4=lm41, gimms=gimms1)
print("\nwrote lai_1deg_1982_1986.npz")
