"""WFDE5 forcing delivery check, evaluated on the model's own C96 points.

Replaces the earlier 1-degree version: putting both fields into 1-degree boxes
compared a C96 cell centre against a box mean of the 0.5-degree source, which in
mountains manufactured +-2 K of difference that was not in the model at all
(temperature sd fell from 0.70 K to 0.0022 K once the comparison moved onto the
model grid).

Sources per field:
  t, q, ps, wind   land_forcing   (what the land was handed each step)
  precip           land_daily     (land_forcing writes precip as fill)
  sw, lw           land_month     (swdn_dir+swdn_dif summed over bands; lwdn)
The source is bilinearly interpolated to the same points; wind is compared
against the source with the gustiness floor applied (gust_const=3.0).

Colour limits are set from the 98th percentile of |difference| per field, so
each panel shows its own real structure instead of a guessed range.

Input : lm4/data/forcing_native_1990.npz
Output: figures/forcing_check_native_1990.png
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature

z = np.load("lm4/data/forcing_native_1990.npz")
lat, lon = z["lat"], np.where(z["lon"] > 180, z["lon"] - 360, z["lon"])
GUST = 3.0

FIELDS = [
    ("t",    z["mod_t"],    z["src_t"],                              1.0,    "Temperature",       "K"),
    ("q",    z["mod_q"],    z["src_q"],                              1e3,    "Specific humidity", "g/kg"),
    ("sw",   z["mod_sw"],   z["src_sw"],                             1.0,    "Downward shortwave", "W/m$^2$"),
    ("lw",   z["mod_lw"],   z["src_lw"],                             1.0,    "Downward longwave",  "W/m$^2$"),
    ("pr",   z["mod_pr"],   z["src_pr"],                             86400., "Precipitation",     "mm/day"),
    # the source wind carries the gustiness floor applied at every step, the way
    # the model does it; flooring the time-mean instead reports +1.64 % that is
    # pure averaging order (sqrt is convex)
    ("wind", z["mod_wind"], z["src_wind_gust"],                      1.0,    "Wind (gustiness per step)", "m/s"),
    ("ps",   z["mod_ps"],   z["src_ps"],                             1e-2,   "Surface pressure",  "hPa"),
]

# Display on a 2-degree grid: the C96 points leave radial streaks at high
# latitude when drawn raw.  Averaging the DIFFERENCE that was computed at the
# native points is safe -- unlike binning the two fields separately, which is
# what manufactured the spurious temperature signal in the first version.
DL = 2.0
NB_LAT, NB_LON = int(180 / DL), int(360 / DL)
blat = 90 - DL / 2 - np.arange(NB_LAT) * DL
blon = -180 + DL / 2 + np.arange(NB_LON) * DL
bi = np.clip(((90.0 - lat) / DL).astype(int), 0, NB_LAT - 1)
bj = np.clip(((lon + 180.0) / DL).astype(int), 0, NB_LON - 1)


def regrid(v, ok):
    s = np.zeros((NB_LAT, NB_LON))
    c = np.zeros((NB_LAT, NB_LON))
    np.add.at(s, (bi[ok], bj[ok]), v[ok])
    np.add.at(c, (bi[ok], bj[ok]), 1.0)
    out = np.full((NB_LAT, NB_LON), np.nan)
    m = c > 0
    out[m] = s[m] / c[m]
    return np.ma.masked_invalid(out)


# One scale for every panel: the difference as a percentage of the field's own
# global mean.  Auto-scaling each panel to its own spread made a 0.002 K
# difference fill the map and read as a large error; a common relative scale
# makes "no colour" mean "below 0.03 %" everywhere and lets the panels be
# compared against each other.
LV = np.array([-1, -0.5, -0.25, -0.1, -0.03, 0.03, 0.1, 0.25, 0.5, 1.0])

print("1990 annual mean at C96 cell centres — model minus source")
print("%-22s %11s %11s %+11s %9s %8s %9s"
      % ("field", "model", "source", "bias", "rel%", "r", "sd(diff)"))
proj = ccrs.PlateCarree()
fig, axes = plt.subplots(3, 3, figsize=(19, 8.6), subplot_kw={"projection": proj},
                         constrained_layout=True)
for k in range(len(FIELDS), axes.size):        # 7 fields, 9 slots
    axes.ravel()[k].axis("off")
cmap = plt.get_cmap("RdBu_r")
norm = mcolors.BoundaryNorm(LV, cmap.N, extend="both")
im = None
for ax, (key, m, s, sc, label, unit) in zip(axes.ravel(), FIELDS):
    a, b = m * sc, s * sc
    ok = np.isfinite(a) & np.isfinite(b)
    d = a - b
    ref = abs(b[ok].mean())
    r = np.corrcoef(a[ok], b[ok])[0, 1]
    print("%-22s %11.4f %11.4f %+11.5f %8.3f%% %8.5f %9.5f"
          % (label, a[ok].mean(), b[ok].mean(), d[ok].mean(),
             d[ok].mean() / ref * 100, r, d[ok].std()))

    ax.set_extent([-180, 180, -60, 85], crs=proj)
    ax.add_feature(cfeature.COASTLINE, lw=0.35)
    im = ax.pcolormesh(blon, blat, regrid(d / ref * 100, ok), cmap=cmap,
                       norm=norm, transform=proj, shading="nearest")
    ax.set_title("%s [%s]   bias %+.4g %s (%+.3f %%)   r %.5f"
                 % (label, unit, d[ok].mean(), unit.replace("$", ""),
                    d[ok].mean() / ref * 100, r), fontsize=9)
    gl = ax.gridlines(draw_labels=True, lw=0.3, alpha=0.4)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {"size": 6.5}
    gl.ylabel_style = {"size": 6.5}

cb = fig.colorbar(im, ax=axes.ravel().tolist(), orientation="horizontal",
                  ticks=LV, shrink=0.35, pad=0.01, aspect=45, extend="both")
cb.ax.tick_params(labelsize=8)
cb.set_label("difference as % of the field's global mean  "
             "(blank = within ±0.03 %)", fontsize=9)
fig.suptitle("WFDE5 forcing delivery — LM4+ offline, 1990 annual mean, model minus source\n"
             "at the C96 cell centres (source interpolated to the same points; no re-binning); "
             "every panel on the same ±1 % scale", fontsize=12.5)
fig.savefig("figures/forcing_check_native_1990.png", dpi=140, bbox_inches="tight")
print("\nwrote figures/forcing_check_native_1990.png")
