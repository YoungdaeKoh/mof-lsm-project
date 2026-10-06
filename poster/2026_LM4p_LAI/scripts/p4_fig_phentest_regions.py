#!/usr/bin/env python3
"""Poster Fig. 3 (panel 4): pilot phenology sensitivity runs, monthly LAI in 2010, six AR6 regions.

input : ../data/{base,tc10,offon}.lai.2010-2010.1deg.nc  one-year runs from the same 2010-01-01 state
          base   tc_crit = 5 C for larix and c3grass (control settings)
          tc10   tc_crit = 10 C (one threshold moved: affects leaf-on AND leaf-off)
          offon  tc_crit = 5 C plus the autumn rule (after solstice, day length < 14 h, tc_pheno < 10 C)
        ../data/gimms_lai_mon_1982_2020.nc  (GIMMS LAI4g, year 2010)
output: ../figures/fig3_phentest_regions.png, ../data/phentest_regions_summary.txt
A run whose file is missing is skipped, so the figure can be drawn before offon has finished.
Monthly means only (poster decision 2026-10-06); regions as in Fig. 2 (regionmask AR6 land).
Note: base/tc10 use the gateBC executable, offon the phenoff one; regional means of the two
executables agree to 1e-6..1e-4 without the new parameters (LM4 notes 13.69).
"""
import os
import warnings
import numpy as np
import netCDF4 as nc
import regionmask
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

YEAR = 2010
REGIONS = [("N.W. North America (NWN)", "NWN"), ("E. Siberia (ESB)", "ESB"), ("Russian Far East (RFE)", "RFE"),
           ("E. North America (ENA)", "ENA"), ("West & Central Europe (WCE)", "WCE"), ("E. Asia (EAS)", "EAS")]
RUNS = [("base", "LM4+ control (5 °C)", "tab:red", "-"),
        ("tc10", "threshold 10 °C", "tab:orange", "--"),
        ("offon", "autumn day-length rule", "tab:blue", "-")]

g = nc.Dataset("../data/gimms_lai_mon_1982_2020.nc")
gname = [v for v in g.variables if g.variables[v].ndim == 3][0]
i0 = (YEAR - 1982) * 12
obs = np.ma.filled(g.variables[gname][i0:i0 + 12].astype("f8"), np.nan)
lat = np.asarray(g.variables["lat"][:]); lon = np.asarray(g.variables["lon"][:])
data = {}
for key, _, _, _ in RUNS:
    f = "../data/%s.lai.%d-%d.1deg.nc" % (key, YEAR, YEAR)
    if os.path.exists(f):
        data[key] = np.ma.filled(nc.Dataset(f).variables["lai"][:].astype("f8"), np.nan)
ok = np.isfinite(obs).all(0)
for v in data.values():
    ok &= np.isfinite(v).all(0)
W = np.cos(np.radians(lat))[:, None] * np.ones((1, lon.size))
ar6 = regionmask.defined_regions.ar6.land
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    m3 = ar6.mask_3D(lon, lat)

out = ["Pilot phenology runs, monthly LAI %d, AR6 regions (common valid cells, cos-lat weights); runs present: %s" % (YEAR, " ".join(data)),
       "gap closed = share of the (base - GIMMS) Sep-Oct gap removed by the run; May-Jun shows the side effect on spring", ""]
fig, axs = plt.subplots(2, 3, figsize=(15.5, 7.2), sharex=True)
mon = np.arange(1, 13)
for (name, ab), ax in zip(REGIONS, axs.ravel()):
    w = W * (ok & m3.sel(region=ar6.map_keys(ab)).values.astype(bool))
    mean = lambda v: np.array([np.nansum(v[k] * w) / w.sum() for k in range(12)])
    o = mean(obs)
    ax.plot(mon, o, color="k", lw=2.4, marker="o", ms=4, label="GIMMS %d" % YEAR)
    out.append("%s  (%d cells)" % (name, int((w > 0).sum())))
    out.append("  month     " + " ".join("%5d" % m for m in mon))
    out.append("  GIMMS     " + " ".join("%5.2f" % x for x in o))
    ser = {}
    for key, label, col, ls in RUNS:
        if key not in data:
            continue
        ser[key] = mean(data[key])
        ax.plot(mon, ser[key], color=col, lw=2, ls=ls, marker="o", ms=3, label=label)
        out.append("  %-9s " % key + " ".join("%5.2f" % x for x in ser[key]))
    so = lambda x: x[8:10].mean(); mj = lambda x: x[4:6].mean()
    gap = so(ser["base"]) - so(o)
    line = "  Sep-Oct mean: GIMMS %.2f" % so(o) + "".join(" | %s %.2f" % (k, so(v)) for k, v in ser.items())
    line += "".join(" | %s closes %+.0f %% of the gap" % (k, (so(ser["base"]) - so(v)) / gap * 100) for k, v in ser.items() if k != "base")
    out.append(line)
    out.append("  May-Jun mean: GIMMS %.2f" % mj(o) + "".join(" | %s %.2f" % (k, mj(v)) for k, v in ser.items()))
    out.append("")
    print(name, "|", line.strip())
    ax.axvspan(8.5, 10.5, color="0.92", lw=0)        # Sep-Oct, the months the rule targets
    ax.set_title(name, fontsize=11, loc="left")
    ax.set_xlim(1, 12); ax.set_ylim(0, None)
    ax.set_xticks(mon); ax.set_xticklabels(list("JFMAMJJASOND"))
    ax.grid(alpha=0.3)
for ax in axs[:, 0]:
    ax.set_ylabel("LAI (m$^2$ m$^{-2}$)")
axs[0, 0].legend(loc="upper left", fontsize=8.5, frameon=False)
fig.suptitle("Pilot sensitivity runs for %d (one year, monthly means); shading = September–October" % YEAR, fontsize=10)
fig.tight_layout(rect=(0, 0, 1, 0.96))
fig.savefig("../figures/fig3_phentest_regions.png", dpi=200)
open("../data/phentest_regions_summary.txt", "w").write("\n".join(out) + "\n")
