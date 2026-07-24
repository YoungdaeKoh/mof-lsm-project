"""PFT composition of high-LAI regions (LM4, JJA 1982).

For each region, PFT share = sum(lai_species over cells) / sum(total_lai).
Left: dominant-PFT map. Right: stacked-bar PFT shares per high-LAI region.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

z = np.load("lm4_pft_jja1982.npz")
lat, lon = z["lat"], z["lon"]
lai_sp = z["lai_sp"]                      # (7, npoints)
SP = [s.decode() if isinstance(s, bytes) else str(s) for s in z["species"]]
tot = np.nansum(lai_sp, axis=0)

COL = {"prioria": "#1b7837", "picea": "#5aae61", "larix": "#a6dba0",
       "acer": "#e08214", "c4grass": "#fee08b", "c3grass": "#c2e699",
       "default": "#cccccc"}

# high-LAI regions (lat0,lat1,lon0,lon1)
REG = {
    "Amazon":       (-12, 5, -75, -50),
    "Congo":        (-6, 5, 12, 30),
    "SE Asia":      (-8, 12, 95, 130),
    "Boreal N.Am":  (50, 65, -130, -70),
    "Boreal Siberia": (52, 66, 60, 130),
    "E US/temperate": (32, 45, -95, -75),
}

def region_share(la0, la1, lo0, lo1):
    m = (lat >= la0) & (lat <= la1) & (lon >= lo0) & (lon <= lo1) & (tot > 1)
    if m.sum() == 0:
        return None, 0
    num = np.nansum(lai_sp[:, m], axis=1)
    den = np.nansum(tot[m])
    return 100 * num / den, int(m.sum())

fig = plt.figure(figsize=(18, 6.5))

# --- dominant PFT map ---
ax = fig.add_subplot(1, 2, 1, projection=ccrs.PlateCarree())
dom = np.argmax(np.nan_to_num(lai_sp), axis=0)
veg = tot > 0.3
codes = np.array([COL[s] for s in SP])
ax.scatter(lon[veg], lat[veg], c=codes[dom[veg]], s=3, transform=ccrs.PlateCarree())
ax.coastlines(linewidth=0.4); ax.set_global()
ax.set_title("Dominant PFT (LM4, JJA 1982)", fontsize=12)
handles = [plt.Line2D([0], [0], marker="o", ls="", mfc=COL[s], mec="none", label=s)
           for s in SP]
ax.legend(handles=handles, loc="lower left", fontsize=8, ncol=2, framealpha=0.9)

# --- stacked bars per region ---
axb = fig.add_subplot(1, 2, 2)
names, shares = [], []
for name, box in REG.items():
    sh, n = region_share(*box)
    if sh is not None:
        names.append("%s\n(n=%d)" % (name, n))
        shares.append(sh)
shares = np.array(shares)                 # (nreg, 7)
bottom = np.zeros(len(names))
for k, s in enumerate(SP):
    axb.bar(names, shares[:, k], bottom=bottom, color=COL[s], label=s)
    bottom += shares[:, k]
axb.set_ylabel("% of total leaf area")
axb.set_title("PFT composition of high-LAI regions", fontsize=12)
axb.set_ylim(0, 100)
axb.legend(fontsize=8, loc="upper right", ncol=2)
axb.tick_params(axis="x", labelsize=8)

fig.suptitle("LM4 PFT breakdown -- JJA 1982", fontsize=14, y=1.0)
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig("lm4_pft_composition.png", dpi=120)
print("wrote lm4_pft_composition.png")
for name, box in REG.items():
    sh, n = region_share(*box)
    if sh is not None:
        top = sorted(zip(SP, sh), key=lambda x: -x[1])[:3]
        print("%-16s n=%-4d  " % (name, n) +
              "  ".join("%s %.0f%%" % (s, v) for s, v in top))
