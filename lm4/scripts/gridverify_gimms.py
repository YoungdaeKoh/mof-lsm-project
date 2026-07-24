"""grid-verify GIMMS LAI4g before using it for comparison. HARD RULE."""
import numpy as np
import netCDF4 as nc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

d = nc.Dataset("/Volumes/data02/LAI/GIMMS_LAI4g_V1.2_1982_2020.nc")
lat = d.variables["latitude"][:]
lon = d.variables["longitude"][:]
t = d.variables["time"][:]
lai = d.variables["lai"]

# --- 1. coordinate metadata ---
print("=== coords ===")
print("lat:", lat[0], "->", lat[-1], "(ascending)" if lat[1] > lat[0] else "(desc)")
print("lon:", lon[0], "->", lon[-1], "0-360" if lon.max() > 180 else "-180-180")
print("shape:", lai.shape, "| _FillValue:", getattr(lai, "_FillValue", None))

# time: days since 1979-01-01 ? index0 should be 1982-01
print("time[0]=%.0f -> %.2f yr since 1979 = %.0f" % (t[0], t[0] / 365.25, 1979 + t[0] / 365.25))
# JJA 1982 = months Jun/Jul/Aug. If index0=1982-01, JJA = 5,6,7
jja_idx = [5, 6, 7]

# --- 5. value/unit sanity + fill ---
a = np.ma.filled(lai[0, :, :].astype("f8"), np.nan)
a[a > 100] = np.nan     # guard against fill (LAI never > ~10)
finite = np.isfinite(a)
print("\n=== values (month 0 = 1982-01) ===")
print("valid %.1f%% (land fraction; ocean should be missing)" % (100 * finite.mean()))
g = a[finite]
print("LAI min=%.3f max=%.3f mean=%.3f" % (g.min(), g.max(), g.mean()))

# --- 2. RAW ARRAY plot, no coords (decisive) ---
jja = np.nanmean(np.stack([np.ma.filled(lai[i].astype("f8"), np.nan)
                           for i in jja_idx]), axis=0)
jja[jja > 100] = np.nan
plt.figure(figsize=(10, 5))
plt.imshow(jja, origin="lower", aspect="auto", cmap="YlGn", vmin=0, vmax=6)
plt.title("GIMMS LAI4g JJA 1982 -- RAW ARRAY (index space, no coords)")
plt.colorbar(label="LAI")
plt.savefig("_gridverify_gimms.png", dpi=110)
print("\nwrote _gridverify_gimms.png  (must show recognizable continents)")

# --- 3. land/sea + JJA field stats ---
jf = jja[np.isfinite(jja)]
print("JJA1982 valid %.1f%%  LAI min=%.3f max=%.3f mean=%.3f" % (
    100 * np.isfinite(jja).mean(), jf.min(), jf.max(), jf.mean()))

# --- 4. latitudinal sanity: tropics green, deserts low ---
# NH summer (JJA): boreal should have moderate LAI, Sahara ~0
def band(a0, b0):
    m = (lat >= a0) & (lat < b0)
    sub = jja[m, :]
    sub = sub[np.isfinite(sub)]
    return sub.mean() if sub.size else np.nan
print("JJA LAI  tropics(-15,15)=%.2f  NH-boreal(50,65)=%.2f  Sahara-lat(18,28)=%.2f" % (
    band(-15, 15), band(50, 65), band(18, 28)))
d.close()
