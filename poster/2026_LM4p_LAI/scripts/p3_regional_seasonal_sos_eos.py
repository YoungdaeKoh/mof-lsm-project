#!/usr/bin/env python3
"""Poster Fig. 2: regional LAI seasonal cycle, LM4p ctl vs GIMMS LAI4g, 1982-2010, with SOS/EOS.

input : ../data/{lm4p_ctl,gimms}_lai_mon_1982_2020.nc  (monthly, 1 deg; n1_lai_clim_anom.ncl)
output: ../data/lai_regional_sos_eos.txt
        ../figures/fig2_regional_seasonal_cycle.png

Method (LM4 notes 13.69, poster decisions 2026-10-06)
  - regional mean: cells valid in every month of both products, cos(lat) weights
  - daily curve: linear interpolation of monthly means placed at mid-month (the model saved
    LAI monthly only, so both products are treated the same way; not true daily data)
  - SOS/EOS: 50 % amplitude threshold, per year. threshold = min + 0.5*(max-min) of that
    year's curve; SOS = last upward crossing before the peak, EOS = first downward crossing
    after the peak. Normalising by each curve's own min/max keeps the different winter
    floors (model 0.88 vs obs 0.26 in the boreal zone) out of the dates.
  - there is no ensemble: mean and +-1 sd are over the 29 years
"""
import warnings
import numpy as np
import netCDF4 as nc
import regionmask
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

Y0, Y1 = 1982, 2010
NY = Y1 - Y0 + 1
REGIONS = [  # title, AR6 abbreviation
    # IPCC AR6 land reference regions (Iturbide et al. 2020), masks from
    # regionmask.defined_regions.ar6.land (v0.13.0); the same polygons are drawn on Fig. 1(c).
    # top row boreal, bottom row temperate (choice and all-region table: notes 13.69,
    # ../data/lai_eos_ar6_regions.txt). Northern Hemisphere only: the calendar-year
    # SOS/EOS logic below does not apply to the Southern Hemisphere.
    ("N.W. North America (NWN)", "NWN"),
    ("E. Siberia (ESB)", "ESB"),
    ("Russian Far East (RFE)", "RFE"),
    ("E. North America (ENA)", "ENA"),
    ("West & Central Europe (WCE)", "WCE"),
    ("E. Asia (EAS)", "EAS"),
]
MID = np.array([15.5, 45.0, 74.5, 105.0, 135.5, 166.0, 196.5, 227.5, 258.0, 288.5, 319.0, 349.5])
DOY = np.arange(1, 366)


def read(fn):
    d = nc.Dataset(fn)
    name = [v for v in d.variables if d.variables[v].ndim == 3][0]
    v = np.ma.filled(d.variables[name][: NY * 12].astype("f8"), np.nan)
    return v, d.variables["lat"][:], d.variables["lon"][:]


def daily(mon, prev_dec, next_jan):
    x = np.concatenate([[MID[-1] - 365.0], MID, [MID[0] + 365.0]])
    y = np.concatenate([[prev_dec], mon, [next_jan]])
    return np.interp(DOY, x, y)


def sos_eos(c):
    lo, hi = c.min(), c.max()
    thr = lo + 0.5 * (hi - lo)
    ip = int(c.argmax())
    up = np.where((c[:-1] < thr) & (c[1:] >= thr))[0]
    dn = np.where((c[:-1] >= thr) & (c[1:] < thr))[0]
    up = up[up < ip]
    dn = dn[dn >= ip]
    s = e = np.nan
    if up.size:
        i = up[-1]
        s = DOY[i] + (thr - c[i]) / (c[i + 1] - c[i])
    if dn.size:
        i = dn[0]
        e = DOY[i] + (c[i] - thr) / (c[i] - c[i + 1])
    return s, e, DOY[ip], lo, hi


def date(doy):
    m = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
    d = int(round(doy))
    k = int(np.searchsorted(np.cumsum(m), d))
    return "%d/%d" % (k + 1, d - np.concatenate([[0], np.cumsum(m)])[k])


mod, lat, lon = read("../data/lm4p_ctl_lai_mon_1982_2020.nc")
obs, _, _ = read("../data/gimms_lai_mon_1982_2020.nc")
ok = np.isfinite(mod).all(0) & np.isfinite(obs).all(0)
W = np.cos(np.radians(lat))[:, None] * np.ones((1, lon.size))
ar6 = regionmask.defined_regions.ar6.land
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    m3 = ar6.mask_3D(np.asarray(lon), np.asarray(lat))

out = ["LM4p ctl vs GIMMS LAI4g (consolidated), %d-%d, regional mean (common valid cells, cos-lat weights)" % (Y0, Y1),
       "daily curve = linear interpolation of monthly means; SOS/EOS = 50 %% amplitude threshold per year; mean +- sd over %d years" % NY,
       "diff = LM4p - GIMMS (days, + = model later)", ""]
fig, axs = plt.subplots(2, 3, figsize=(15.5, 7.2), sharex=True)
for (name, ab), ax in zip(REGIONS, axs.ravel()):
    r = ok & m3.sel(region=ar6.map_keys(ab)).values.astype(bool)
    w = W * r
    res = {}
    for key, v in (("LM4p", mod), ("GIMMS", obs)):
        ts = np.array([np.nansum(v[t] * w) / w.sum() for t in range(NY * 12)]).reshape(NY, 12)
        cur, st = [], []
        for y in range(NY):
            pd = ts[y - 1, 11] if y > 0 else ts[y, 11]
            nj = ts[y + 1, 0] if y < NY - 1 else ts[y, 0]
            c = daily(ts[y], pd, nj)
            cur.append(c)
            st.append(sos_eos(c))
        res[key] = (ts, np.array(cur), np.array(st))
    out.append("%s  (%d cells)" % (name, int(r.sum())))
    out.append("  month        " + " ".join("%5d" % (k + 1) for k in range(12)))
    for key in ("LM4p", "GIMMS"):
        out.append("  %-5s clim   " % key + " ".join("%5.2f" % x for x in res[key][0].mean(0)))
    for key in ("LM4p", "GIMMS"):
        s = res[key][2]
        out.append("  %-5s SOS %6.1f +- %4.1f (%s)  EOS %6.1f +- %4.1f (%s)  peak day %5.1f  season length %5.1f  min %.2f max %.2f  valid years SOS %d EOS %d"
                   % (key, np.nanmean(s[:, 0]), np.nanstd(s[:, 0]), date(np.nanmean(s[:, 0])),
                      np.nanmean(s[:, 1]), np.nanstd(s[:, 1]), date(np.nanmean(s[:, 1])),
                      s[:, 2].mean(), np.nanmean(s[:, 1] - s[:, 0]), s[:, 3].mean(), s[:, 4].mean(),
                      np.isfinite(s[:, 0]).sum(), np.isfinite(s[:, 1]).sum()))
    dm, do = res["LM4p"][2], res["GIMMS"][2]
    ds, de = dm[:, 0] - do[:, 0], dm[:, 1] - do[:, 1]
    out.append("  diff  SOS %+6.1f +- %4.1f d   EOS %+6.1f +- %4.1f d   season length %+6.1f d   (years with model later: SOS %d/%d, EOS %d/%d)"
               % (np.nanmean(ds), np.nanstd(ds), np.nanmean(de), np.nanstd(de), np.nanmean(de - ds),
                  (ds > 0).sum(), np.isfinite(ds).sum(), (de > 0).sum(), np.isfinite(de).sum()))
    out.append("")
    print("%-38s dSOS %+6.1f +- %4.1f  dEOS %+6.1f +- %4.1f  (LM4p EOS %s, GIMMS EOS %s)"
          % (name, np.nanmean(ds), np.nanstd(ds), np.nanmean(de), np.nanstd(de),
             date(np.nanmean(dm[:, 1])), date(np.nanmean(do[:, 1]))))

    for key, col in (("GIMMS", "k"), ("LM4p", "tab:red")):
        c, s = res[key][1], res[key][2]
        m, sd = c.mean(0), c.std(0)
        ax.fill_between(DOY, m - sd, m + sd, color=col, alpha=0.18, lw=0)
        ax.plot(DOY, m, color=col, lw=2, label=key if key == "GIMMS" else "LM4+")
        for j, ls in ((0, ":"), (1, "--")):
            ax.axvline(np.nanmean(s[:, j]), color=col, ls=ls, lw=1.2)
    ax.set_title(name, fontsize=11, loc="left")
    ax.text(0.02, 0.95, "$\\Delta$SOS %+.0f d\n$\\Delta$EOS %+.0f d" % (np.nanmean(ds), np.nanmean(de)),
            transform=ax.transAxes, va="top", fontsize=10,
            bbox=dict(fc="white", ec="0.6", lw=0.6))
    ax.set_xlim(1, 365)
    ax.set_ylim(0, None)
    ax.set_xticks([1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335])
    ax.set_xticklabels(list("JFMAMJJASOND"))
    ax.grid(alpha=0.3)
for ax in axs[:, 0]:
    ax.set_ylabel("LAI (m$^2$ m$^{-2}$)")
axs[0, 0].legend(loc="upper right", fontsize=9, frameon=False)
fig.suptitle("LAI seasonal cycle %d–%d: mean ± 1 s.d. over %d years (monthly means, linearly interpolated).  dotted = SOS, dashed = EOS (50 %% amplitude)"
             % (Y0, Y1, NY), fontsize=10)
fig.tight_layout(rect=(0, 0, 1, 0.96))
fig.savefig("../figures/fig2_regional_seasonal_cycle.png", dpi=200)
open("../data/lai_regional_sos_eos.txt", "w").write("\n".join(out) + "\n")
