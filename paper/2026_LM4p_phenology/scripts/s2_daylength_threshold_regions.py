#!/usr/bin/env python3
"""SI figure: where the day-length thresholds come from (13 h boreal: larix, C3 grass; 12 h temperate: acer).

Same calculation as poster/2026_LM4p_LAI/scripts/p6_daylength_at_eos_percell.py: GIMMS LAI4g 1982-2010 monthly
climatology, cells north of 20N with amplitude >= 0.5, EOS = 50 % amplitude crossing after the peak (monthly means
interpolated to days), day length on that date at the cell's latitude (Cooper declination + sunrise equation).
(a) map of day length at observed EOS with the six AR6 regions used (boreal NWN, ESB, RFE; temperate ENA, WCE, EAS);
(b) distribution per region (box p25-p75, whiskers p10-p90, median labelled) with the 13 h and 12 h thresholds.
output: ../figures/s2_daylength_threshold_regions.png, ../data/s2_daylength_threshold_regions.txt
"""
import warnings
import numpy as np
import netCDF4 as nc
import regionmask
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

D = np.arange(1, 366.0)
MID = np.array([15.5, 45, 74.5, 105, 135.5, 166, 196.5, 227.5, 258, 288.5, 319, 349.5])
g = nc.Dataset("../../../poster/2026_LM4p_LAI/data/gimms_lai_clim_1982_2010.nc")
clim = np.ma.filled(g["clim"][:].astype("f8"), np.nan)
lat = np.asarray(g["lat"][:]); lon = np.asarray(g["lon"][:])
ok = np.isfinite(clim).all(0) & (lat[:, None] > 20) & ((clim.max(0) - clim.min(0)) >= 0.5)
dl = np.full(ok.shape, np.nan)
for i, j in zip(*np.where(ok)):
    m = clim[:, i, j]
    c = np.interp(D, np.r_[MID[-1] - 365, MID, MID[0] + 365], np.r_[m[-1], m, m[0]])
    thr = c.min() + 0.5 * (c.max() - c.min()); ip = int(c.argmax())
    dn = [k for k in range(ip, 364) if c[k] >= thr > c[k + 1]]
    if not dn:
        continue
    k = dn[0]; e = D[k] + (c[k] - thr) / (c[k] - c[k + 1])
    decl = np.radians(23.44) * np.sin(2 * np.pi * (284 + e) / 365)
    dl[i, j] = 24 / np.pi * np.arccos(np.clip(-np.tan(np.radians(lat[i])) * np.tan(decl), -1, 1))

ar6 = regionmask.defined_regions.ar6.land
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    m3 = ar6.mask_3D(lon, lat)
GROUPS = [("Boreal → 13 h (larch, C3 grass)", "#2166ac", 13, ("NWN", "ESB", "RFE")),
          ("Temperate → 12 h (broadleaf deciduous, acer)", "#d6604d", 12, ("ENA", "WCE", "EAS"))]
stat = {}
out = ["Day length at observed EOS (GIMMS LAI4g 1982-2010 climatology, amplitude >= 0.5, north of 20N)",
       "region  n     p10   p25   median p75   p90   (h) | AR6 bounds lon/lat"]
for _, _, _, regs in GROUPS:
    for r in regs:
        v = dl[m3.sel(region=ar6.map_keys(r)).values.astype(bool) & np.isfinite(dl)]
        stat[r] = np.percentile(v, [10, 25, 50, 75, 90])
        b = ar6[r].polygon.bounds
        out.append("%-6s %5d  %s | %.0f..%.0f E, %.0f..%.0f N" % (r, v.size, " ".join("%5.2f" % q for q in stat[r]), b[0], b[2], b[1], b[3]))
open("../data/s2_daylength_threshold_regions.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))

fig = plt.figure(figsize=(13, 6.4))
proj = ccrs.PlateCarree(central_longitude=180)
ax = fig.add_axes([0.04, 0.47, 0.90, 0.50], projection=proj)
ax.set_extent([-180, 180, 15, 80], crs=proj)
ax.add_feature(cfeature.LAND, facecolor="0.92"); ax.coastlines(lw=0.4, color="0.4")
im = ax.pcolormesh(lon, lat, np.ma.masked_invalid(dl), cmap="viridis", vmin=10, vmax=15, transform=ccrs.PlateCarree(), shading="auto")
for _, col, _, regs in GROUPS:
    for r in regs:
        x, y = ar6[r].polygon.exterior.xy
        ax.plot(x, y, color=col, lw=2.2, transform=ccrs.PlateCarree())
        cx, cy = ar6[r].centroid
        ax.text(cx, cy, "%s\n%.2f h" % (r, stat[r][2]), transform=ccrs.PlateCarree(), ha="center", va="center", fontsize=9,
                weight="bold", color=col, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
gl = ax.gridlines(draw_labels=True, lw=0.3, color="0.6", ls=":", xlocs=range(-180, 181, 60), ylocs=range(20, 81, 20))
gl.top_labels = False; gl.right_labels = False
ax.set_title("(a) Day length on the observed EOS date (GIMMS LAI4g 1982–2010)", loc="left", fontsize=11)
cb = fig.colorbar(im, cax=ax.inset_axes([1.01, 0, 0.012, 1]), extend="both"); cb.set_label("h")

b = fig.add_axes([0.20, 0.06, 0.60, 0.33])
yl, y = [], 0
for name, col, thr, regs in GROUPS:
    for r in regs:
        q = stat[r]
        b.plot([q[0], q[4]], [y, y], color=col, lw=1.2)
        b.add_patch(plt.Rectangle((q[1], y - 0.3), q[3] - q[1], 0.6, fc=col, alpha=0.35, ec=col))
        b.plot([q[2], q[2]], [y - 0.3, y + 0.3], color=col, lw=2.4)
        b.text(q[4] + 0.08, y, "%.2f h" % q[2], va="center", fontsize=9, color=col)
        yl.append(r); y -= 1
    y -= 0.5
for name, col, thr, _ in GROUPS:
    b.axvline(thr, color=col, ls="--", lw=1.3)
    b.text(thr + (0.08 if thr == 13 else -0.08), 0.75, name, color=col, fontsize=9, ha="left" if thr == 13 else "right", va="bottom")
b.set_yticks([0, -1, -2, -3.5, -4.5, -5.5]); b.set_yticklabels(yl)
b.set_ylim(-6.2, 1.5); b.set_xlim(9.5, 15.5); b.set_xlabel("Day length at observed EOS (h); box p25–p75, whiskers p10–p90")
b.set_title("(b) Regional distribution and the leaf-off thresholds", loc="left", fontsize=11)
b.grid(axis="x", alpha=0.3)
fig.savefig("../figures/s2_daylength_threshold_regions.png", dpi=200, bbox_inches="tight")
