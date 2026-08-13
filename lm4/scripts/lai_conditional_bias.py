"""Is the LAI bias a function of how much leaf area is actually there?

The mean map shows the model high nearly everywhere, but the size of the excess
is not uniform, and Australia looks almost unbiased while southern South America
is deep red.  Two readings fit that picture and they lead to different places:

  * the model is wrong in particular places, or
  * the model over-responds at a particular level of leaf area, and the map is
    showing where that level occurs.

Conditioning on the observation separates them.  For each bin of GIMMS LAI, take
the model's mean LAI in the cells that fall in that bin.  A model that is simply
scaled up gives a straight line above 1:1; a model that saturates late, or that
runs away once vegetation is dense, gives a curve.  Done per region it also
shows whether a region is unusual in itself or only unusual in how much leaf
area it has.

Regions are the seven from lai_trend_regions.py plus southern South America,
which the mean map flags strongly and which the earlier set had no box for.

Window 1990-2010 MJJAS, the drift-free years, on the common 1-degree grid.

Inputs : lm4/data/lm4_lai_1982_2010.npz, lm4/data/gimms_1deg_1982_2010.npz
Output : figures/lai_conditional_bias.png, lm4/data/lai_conditional_bias.csv
"""
import numpy as np
import matplotlib.pyplot as plt

NLAT, NLON = 180, 360
lat1 = 89.5 - np.arange(NLAT)
lon1 = -179.5 + np.arange(NLON)
YEARS = np.arange(1990, 2011)
EDGES = np.array([0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0])

REGIONS = [
    ("Global land",   None,                 "#333333"),
    ("Amazon",        (-10, 5, -70, -50),   "#1b9e77"),
    ("S. South America", (-35, -20, -65, -45), "#d95f02"),
    ("Congo",         (-5, 5, 12, 30),      "#7570b3"),
    ("SE Asia",       (-10, 10, 95, 140),   "#e7298a"),
    ("Australia",     (-35, -15, 115, 150), "#66a61e"),
    ("Siberia",       (55, 70, 60, 140),    "#e6ab02"),
    ("East Asia",     (20, 50, 100, 145),   "#a6761d"),
    ("North America", (30, 55, -125, -70),  "#666666"),
]

z = np.load("lm4/data/lm4_lai_1982_2010.npz")
g = np.load("lm4/data/gimms_1deg_1982_2010.npz")
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


M = np.nanmean(np.stack([bin_model(z["mjjas_%d" % y]) for y in YEARS]), axis=0)
G = np.nanmean(np.stack([g["mjjas_%d" % y] for y in YEARS]), axis=0)
common = np.isfinite(M) & np.isfinite(G)
LATG = lat1[:, None] * np.ones((1, NLON))
LONG = np.ones((NLAT, 1)) * lon1[None, :]
print("common 1-degree cells: %d" % common.sum())

rows, curves = [], {}
print("\n%-18s %6s %7s %7s %8s %8s" %
      ("region", "cells", "GIMMS", "LM4", "bias", "bias%"))
for name, bx, _ in REGIONS:
    sel = common.copy()
    if bx is not None:
        la0, la1, lo0, lo1 = bx
        sel &= (LATG >= la0) & (LATG < la1) & (LONG >= lo0) & (LONG < lo1)
    if sel.sum() < 30:
        continue
    go, mo = G[sel], M[sel]
    print("%-18s %6d %7.3f %7.3f %+8.3f %+7.1f%%"
          % (name, sel.sum(), go.mean(), mo.mean(), mo.mean() - go.mean(),
             100 * (mo.mean() - go.mean()) / go.mean()))

    # conditional model mean per observed-LAI bin
    xs, ys, ns = [], [], []
    for k in range(EDGES.size - 1):
        b = (go >= EDGES[k]) & (go < EDGES[k + 1])
        if b.sum() >= 15:                       # bins too thin to trust are dropped
            xs.append(0.5 * (EDGES[k] + EDGES[k + 1]))
            ys.append(mo[b].mean())
            ns.append(b.sum())
    curves[name] = (np.array(xs), np.array(ys), np.array(ns))
    for x, y, n in zip(xs, ys, ns):
        rows.append([x, y, n, go.mean(), mo.mean()])

np.savetxt("lm4/data/lai_conditional_bias.csv", np.array(rows), delimiter=",",
           header="gimms_bin_centre,lm4_mean_in_bin,ncells,region_gimms_mean,region_lm4_mean",
           comments="", fmt="%.5f")

# ---- how much of a region's bias is explained by its LAI level alone --------
gx, gy, _ = curves["Global land"]
print("\nregion bias vs what the global curve predicts at the same LAI level")
print("%-18s %8s %10s %10s" % ("region", "bias", "predicted", "residual"))
for name, bx, _ in REGIONS[1:]:
    if name not in curves:
        continue
    sel = common & (LATG >= bx[0]) & (LATG < bx[1]) & (LONG >= bx[2]) & (LONG < bx[3])
    go, mo = G[sel], M[sel]
    pred = np.interp(go, gx, gy)                # global response at that obs level
    print("%-18s %+8.3f %+10.3f %+10.3f"
          % (name, mo.mean() - go.mean(), pred.mean() - go.mean(),
             mo.mean() - pred.mean()))

# ------------------------------------------------------------------ figure ---
fig, axes = plt.subplots(1, 2, figsize=(15, 6.4))

ax = axes[0]
h = ax.hist2d(G[common], M[common], bins=[np.arange(0, 7.05, 0.15),
                                          np.arange(0, 7.05, 0.15)],
              cmap="Greys", norm="log")
fig.colorbar(h[3], ax=ax, label="1° cells")
lim = [0, 7]
ax.plot(lim, lim, "-", color="#2166ac", lw=2, label="1:1")
gx_, gy_, _ = curves["Global land"]
ax.plot(gx_, gy_, "o-", color="#b2182b", lw=2.4, ms=6, label="global conditional mean")
ax.set_xlim(lim)
ax.set_ylim(lim)
ax.set_xlabel("GIMMS LAI4g  [m$^2$/m$^2$]", fontsize=12)
ax.set_ylabel("LM4+ LAI  [m$^2$/m$^2$]", fontsize=12)
ax.set_title("(a) every land cell — the model against the observation",
             fontsize=13, loc="left")
ax.legend(fontsize=10, loc="upper left")
ax.grid(alpha=0.3, lw=0.5)

ax = axes[1]
ax.plot(lim, lim, "-", color="#2166ac", lw=2, zorder=1)
for name, bx, col in REGIONS:
    if name not in curves:
        continue
    x, y, n = curves[name]
    ax.plot(x, y, "o-" if bx else "o--", color=col, lw=2.0 if bx else 3.0, ms=5,
            label=name, zorder=3)
ax.set_xlim(lim)
ax.set_ylim([0, 8])          # S. South America sits above 6 at an observed 1-2
ax.set_xlabel("GIMMS LAI4g  [m$^2$/m$^2$]", fontsize=12)
ax.set_ylabel("LM4+ LAI in that bin  [m$^2$/m$^2$]", fontsize=12)
ax.set_title("(b) the same curve per region — above 1:1 is over-prediction",
             fontsize=13, loc="left")
ax.legend(fontsize=9, loc="lower right", ncol=2, framealpha=0.95)
ax.grid(alpha=0.3, lw=0.5)

fig.suptitle("MJJAS LAI 1990–2010: what the model produces where the observation "
             "says a given amount of leaf area\n"
             "bins with fewer than 15 cells are dropped;  common 1° cells",
             fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.92])
fig.savefig("figures/lai_conditional_bias.png", dpi=140)
print("\nwrote figures/lai_conditional_bias.png")
