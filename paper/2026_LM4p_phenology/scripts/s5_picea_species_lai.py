#!/usr/bin/env python3
"""Picea-dominated cells: is the autumn LAI of the cell carried by picea itself or by the deciduous species mixed in?

Model: land_month_by_species lai (species contributions; their sum equals the cell LAI, checked July 2010 median
ratio 1.000) for CTRL (base) and DL13/12 (dayl_d), 2010, C96 cells (quasi equal area -> plain mean).
Cells: July CTRL picea share >= 50 %, latitude bands 40-50 / 50-60 / 60-70N and AR6 ESB.
Obs: GLASS and GIMMS 2010 monthly, 1-deg box containing each C96 centre.
Prints the monthly curves of the cell total, picea, and the other species, and the Jul -> Oct change.
output: ../figures/s5_picea_species_lai.png, ../data/s5_picea_species_lai.txt
"""
import glob
import shapely
import numpy as np
from netCDF4 import Dataset
import regionmask
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = "/Volumes/data02/LM4P/cases/phentest_2010/"
P = "../../../poster/2026_LM4p_LAI/data/"
SP = ["prioria", "picea", "larix", "acer", "c4grass", "c3grass", "default"]


def read(run):
    la, lo, v = [], [], []
    for f in sorted(glob.glob(R + run + "/20100101.land_month_by_species.tile*.nc")):
        with Dataset(f) as A:
            A.set_auto_mask(False)
            la.append(A["geolat_t"][:]); lo.append(A["geolon_t"][:]); v.append(A["lai"][:].astype("f8"))
    v = np.concatenate(v, 2); v[np.abs(v) > 1e10] = np.nan
    lo = np.concatenate(lo); return np.concatenate(la), np.where(lo > 180, lo - 360, lo), v


lat, lon, ctl = read("base")
_, _, dl = read("dayl_d")
obs = {}
for k, f, y0 in (("GLASS", "glass_lai_modis_monthly_1deg_2001_2020.nc", 2001), ("GIMMS", "gimms_lai_mon_1982_2020.nc", 1982)):
    with Dataset(P + f) as A:
        x = np.ma.filled(A["lai"][(2010 - y0) * 12:(2010 - y0) * 12 + 12].astype("f8"), np.nan)
        assert np.isclose(A["lat"][0], -89.5) and np.isclose(A["lon"][0], -179.5)
    x[np.abs(x) > 100] = np.nan
    obs[k] = x[:, np.clip(((lat + 90) // 1).astype(int), 0, 179), np.clip(((lon + 180) // 1).astype(int), 0, 359)]

tot = np.nansum(ctl, 1)
ip = SP.index("picea")
share = ctl[6, ip] / np.where(tot[6] > 0, tot[6], np.nan)
good = np.isfinite(share) & np.isfinite(obs["GLASS"]).all(0) & np.isfinite(obs["GIMMS"]).all(0)
esb = shapely.contains_xy(regionmask.defined_regions.ar6.land["ESB"].polygon, lon, lat)   # unstructured C96 points
GROUPS = [("40-50N", (lat >= 40) & (lat < 50)), ("50-60N", (lat >= 50) & (lat < 60)), ("60-70N", (lat >= 60) & (lat < 70)), ("ESB", esb)]

out = ["Picea-dominated cells (July CTRL picea share >= 50 %), 2010 monthly LAI; Jul->Oct change (m2/m2 and % of July)"]
fig, axs = plt.subplots(1, 4, figsize=(15, 3.8), sharey=False)
M = np.arange(1, 13)
for ax, (name, sel) in zip(axs, GROUPS):
    m = good & sel & (share >= 0.5)
    c = {}
    for run, v in (("CTRL", ctl), ("DL13/12", dl)):
        c[run + " total"] = np.nanmean(np.nansum(v[:, :, m], 1), 1)
        c[run + " picea"] = np.nanmean(v[:, ip, m], 1)
        c[run + " others"] = c[run + " total"] - c[run + " picea"]
    for k in obs:
        c[k] = np.nanmean(obs[k][:, m], 1)
    out.append("")
    out.append("%s  n %d C96 cells, mean picea share %.2f" % (name, m.sum(), np.nanmean(share[m])))
    out.append("%-14s " % "" + " ".join("%5s" % s for s in "J F M A M J J A S O N D".split()) + " | Jul->Oct")
    for k, v in c.items():
        out.append("%-14s " % k + " ".join("%5.2f" % x for x in v) + " | %+5.2f (%+4.0f %%)" % (v[9] - v[6], 100 * (v[9] - v[6]) / v[6]))
    ax.plot(M, c["GLASS"], "k-", lw=2, label="GLASS"); ax.plot(M, c["GIMMS"], "k--", lw=1.5, label="GIMMS")
    ax.plot(M, c["CTRL total"], color="#1f77b4", lw=2, label="CTRL cell total")
    ax.plot(M, c["DL13/12 total"], color="#d62728", lw=2, label="DL13/12 cell total")
    ax.plot(M, c["CTRL picea"], color="#08519c", lw=1.5, ls=":", label="picea part (CTRL = DL13/12)")
    ax.plot(M, c["DL13/12 others"], color="#d62728", lw=1.2, ls="-.", label="other species, DL13/12")
    ax.plot(M, c["CTRL others"], color="#1f77b4", lw=1.2, ls="-.", label="other species, CTRL")
    ax.set_title("%s (n = %d)" % (name, m.sum()), loc="left", fontsize=10)
    ax.set_xticks(M); ax.set_xticklabels(list("JFMAMJJASOND")); ax.grid(alpha=0.3)
axs[0].set_ylabel("LAI (m$^2$ m$^{-2}$)")
axs[-1].legend(fontsize=7.5, frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0))
fig.suptitle("Picea-dominated cells, 2010: cell LAI split into the picea part and the other species", x=0.01, ha="left", fontsize=11)
fig.savefig("../figures/s5_picea_species_lai.png", dpi=170, bbox_inches="tight")
open("../data/s5_picea_species_lai.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
