"""River discharge at East Asian mouths: LM4+ against gauge observations.

This is the axis the project is actually about.  Everything else diagnosed so far
stops at the land surface; discharge is what the land delivers to the ocean, and
in a coupled model it is what sets coastal salinity and stratification.

Observations are Dai et al. (2025), the update to Dai & Trenberth (2002): monthly
flow at the farthest downstream station of 936 rivers, 1900-2024.  Two of its
fields matter here and are easy to misuse:

  FLOW        m3/s at the *station*, which sits upstream of the mouth
  ratio_m2s   mouth-to-station flow ratio, from a routing model

Comparing the model's mouth cell against FLOW without applying ratio_m2s would
compare two different points on the river.  The ratio is applied.

Matching a gauge to a cubed-sphere cell is the other trap, and at C96 it cannot
always be done.  A cell is about 100 km, so the search takes the largest flow
within a radius rather than the nearest cell -- a mouth is by construction the
local maximum of river flow, so this finds the channel and not its floodplain.
Two failure modes then have to be caught rather than reported as results:

  * several gauges landing on one cell.  The Xijiang, Beijiang and Dongjiang all
    empty into the Pearl River delta, which the model resolves as a single cell,
    so they are summed and compared as one system.  Reporting them separately
    would show the model three times too large on two of them.
  * a gauge grabbing a different river.  The Huai mouth sits within 2.5 deg of
    the Yangtze channel, and the search finds the Yangtze.  Matches beyond
    MAX_DIST are dropped.

Inputs : lm4/data/discharge_1979_2023.npz
         /Volumes/data02/runoff/Dai2025/coastal-stns-Vol-monthly.updated-Aug2025.nc
Output : figures/discharge_vs_dai_eastasia.png, lm4/data/discharge_vs_dai.csv
"""
import numpy as np
import netCDF4 as nc
import matplotlib.pyplot as plt

DAI = ("/Volumes/data02/runoff/Dai2025/"
       "coastal-stns-Vol-monthly.updated-Aug2025.nc")
NPZ = "lm4/data/discharge_1979_2023.npz"
Y0, Y1 = 1979, 2023
SEARCH_DEG = 2.0           # radius of the mouth search, degrees
MAX_DIST = 1.75            # beyond this the match is not the same river;
                           # a C96 cell is ~1 deg, so this allows the channel to
                           # sit a cell or so from the gauge's mouth coordinate

# ------------------------------------------------------------------ model ---
z = np.load(NPZ)
mlat, mlon = z["lat"], z["lon"]                 # (6,96,96)
area = z["cell_area"]                           # (6,96,96) m2
myears = z["years"]
sel = (myears >= Y0) & (myears <= Y1)
# dis_liq is kg/m2/s over the cell; x area / density -> m3/s leaving for the ocean
Q = z["dis_liq"][sel] * area[None, None, :, :, :] / 1000.0
qclim = np.nanmean(Q, axis=0)                   # (12,6,96,96) monthly climatology
qann = np.nanmean(qclim, axis=0)                # (6,96,96) annual mean

# ------------------------------------------------------------ observations --
d = nc.Dataset(DAI)


def txt(var, i):
    """netCDF char arrays here are null-padded, and matplotlib draws a null as a
    box, so strip them explicitly rather than relying on strip()."""
    raw = b"".join(d.variables[var][i].astype("S1")).decode("utf8", "ignore")
    return raw.replace("\x00", "").strip()


n = len(d.dimensions["station"])
riv = [txt("riv_name", i) for i in range(n)]
stn = [txt("stn_name", i) for i in range(n)]
lat_m = np.array(d.variables["lat_mou"][:])
lon_m = np.array(d.variables["lon_mou"][:])
lon_m = np.where(lon_m > 180, lon_m - 360, lon_m)
ratio = np.array(d.variables["ratio_m2s"][:])
vol = np.array(d.variables["vol_stn"][:])
tt = np.array(d.variables["time"][:]).astype(int)     # YYYYMM
flow = np.ma.filled(d.variables["FLOW"][:].astype("f8"), np.nan)   # (time,station)
d.close()

oyr, omo = tt // 100, tt % 100
osel = (oyr >= Y0) & (oyr <= Y1)

# East Asian mouths, largest first
ea = np.where((lat_m >= 20) & (lat_m <= 46) & (lon_m >= 100) & (lon_m <= 145))[0]
ea = ea[np.argsort(-vol[ea])][:10]

# --- first pass: find each gauge's model cell -------------------------------
match = {}
for i in ea:
    m = osel & np.isfinite(flow[:, i])
    if m.sum() < 60:                              # fewer than five years
        print("skip %-14s observations too short (%d months)" % (riv[i][:12], m.sum()))
        continue
    dist = np.sqrt(((mlat - lat_m[i]) * 1.0) ** 2 +
                   ((mlon - lon_m[i]) * np.cos(np.deg2rad(lat_m[i]))) ** 2)
    cand = np.where(dist <= SEARCH_DEG, qann, -np.inf)
    if not np.isfinite(cand).any():
        print("skip %-14s no model cell within %.1f deg" % (riv[i][:12], SEARCH_DEG))
        continue
    j = np.unravel_index(np.nanargmax(cand), cand.shape)
    if dist[j] > MAX_DIST:
        print("skip %-14s nearest channel is %.2f deg away, not the same river"
              % (riv[i][:12], dist[j]))
        continue
    o_clim = np.array([np.nanmean(flow[m & (omo == k + 1), i]) for k in range(12)])
    match.setdefault(j, []).append((i, o_clim * ratio[i], dist[j]))

# --- second pass: gauges sharing a cell are one system ----------------------
print("\nDai et al. (2025) vs LM4+, %d-%d\n" % (Y0, Y1))
print("%-30s %6s %10s %10s %8s %7s" %
      ("river (system)", "dist", "obs m3/s", "model", "model/obs", "r_seas"))
rows, series = [], []
for j, members in sorted(match.items(), key=lambda kv: -qann[kv[0]]):
    name = " + ".join(riv[i] for i, _, _ in members)
    o_clim = np.sum([c for _, c, _ in members], axis=0)
    o_ann = np.nanmean(o_clim)
    m_clim = qclim[(slice(None),) + j]
    m_ann = np.nanmean(m_clim)
    dmin = min(dd for _, _, dd in members)
    r = np.corrcoef(o_clim, m_clim)[0, 1]
    tag = name if len(members) == 1 else "%s (one C96 cell)" % name
    print("%-30s %6.2f %10.0f %10.0f %8.2f %7.2f"
          % (name[:30], dmin, o_ann, m_ann, m_ann / o_ann, r))
    rows.append([name, len(members), dmin, o_ann, m_ann, m_ann / o_ann, r])
    series.append((tag, o_clim, m_clim, o_ann, m_ann, r))

with open("lm4/data/discharge_vs_dai.csv", "w") as fh:
    fh.write("river,station,lat_mouth,lon_mouth,dist_deg,obs_m3s,model_m3s,ratio,r_season\n")
    for r_ in rows:
        fh.write("%s,%d,%.3f,%.2f,%.2f,%.4f,%.4f\n" % tuple(r_))

# ----------------------------------------------------------------- figure ---
nrow = int(np.ceil(len(series) / 3))
fig, axes = plt.subplots(nrow, 3, figsize=(14, 3.8 * nrow), squeeze=False,
                         constrained_layout=True)
mn = np.arange(1, 13)
for ax, (name, o, m, oa, ma, r) in zip(axes.ravel(), series):
    ax.plot(mn, o, "s-", color="#238b45", lw=2, ms=5, label="Dai et al. (obs)")
    ax.plot(mn, m, "o-", color="#08519c", lw=2, ms=5, label="LM4+")
    ax.set_title("%s\nmodel/obs %.2f    r = %.2f" % (name, ma / oa, r),
                 fontsize=11.5, loc="left")
    ax.set_xlim(1, 12)
    ax.set_xticks([1, 4, 7, 10])
    ax.set_xticklabels(["Jan", "Apr", "Jul", "Oct"])
    ax.grid(alpha=0.3, lw=0.5)
    ax.set_ylabel("m$^3$/s", fontsize=11)
for ax in axes.ravel()[len(series):]:
    ax.axis("off")
axes[0, 0].legend(fontsize=10)
fig.suptitle("River discharge at East Asian mouths, %d–%d monthly climatology\n"
             "observations are station flow scaled to the mouth by Dai's "
             "mouth-to-station ratio" % (Y0, Y1), fontsize=14)
fig.savefig("figures/discharge_vs_dai_eastasia.png", dpi=140)
print("\nwrote figures/discharge_vs_dai_eastasia.png")
