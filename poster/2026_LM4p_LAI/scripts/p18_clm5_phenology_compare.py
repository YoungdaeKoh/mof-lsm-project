#!/usr/bin/env python3
"""CLM5 (BGC offline, WFDE5, release-clm5.0.37) vs LM4+ vs GIMMS: seasonal cycle and SOS/EOS, 1982-2010.

CLM5 leaf-off rule = day length < 10.92 h after the summer solstice (no temperature; CNPhenologyMod.F90 L956-957);
LM4+ = smoothed canopy temperature < 5 / 10 C. Same method as Fig. 2 (p3): regional mean (common valid cells, cos-lat
weights), monthly means interpolated to days, SOS/EOS = 50 % amplitude crossing per year.
Inputs: CLM5 TLAI /Volumes/data02/cesm2/clm5_prod_TLAI/clm5_TLAI.YYYY.nc (f09 0.9x1.25, lat ascending, lon 0-360;
        grid-verified 2026-10-08), regridded to the 1-deg GIMMS grid by nearest neighbour;
        ../data/{lm4p_ctl,gimms}_lai_mon_1982_2020.nc (1 deg).
Output: ../figures/fig_clm5_lm4_gimms_regions.png, ../data/clm5_lm4_gimms_sos_eos.txt
"""
import warnings
import numpy as np
import netCDF4 as nc
import regionmask
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

Y0, Y1 = 1982, 2010; NY = Y1 - Y0 + 1
MID = np.array([15.5, 45.0, 74.5, 105.0, 135.5, 166.0, 196.5, 227.5, 258.0, 288.5, 319.0, 349.5]); DOY = np.arange(1, 366)
REG = [("N. Europe (NEU)", "NEU"), ("Russian Far East (RFE)", "RFE"), ("N.W. North America (NWN)", "NWN"), ("E. Siberia (ESB)", "ESB"),
       ("E. North America (ENA)", "ENA"), ("West & Central Europe (WCE)", "WCE"), ("E. Asia (EAS)", "EAS")]


def read1(fn):
    d = nc.Dataset(fn); name = [v for v in d.variables if d.variables[v].ndim == 3][0]
    return np.ma.filled(d.variables[name][: NY * 12].astype("f8"), np.nan), np.asarray(d["lat"][:]), np.asarray(d["lon"][:])


mod, lat, lon = read1("../data/lm4p_ctl_lai_mon_1982_2020.nc")
obs, _, _ = read1("../data/gimms_lai_mon_1982_2020.nc")
# CLM5: 29 yearly files -> nearest neighbour onto the 1-deg grid
c = []
for y in range(Y0, Y1 + 1):
    d = nc.Dataset("/Volumes/data02/cesm2/clm5_prod_TLAI/clm5_TLAI.%d.nc" % y)
    c.append(np.ma.filled(d["TLAI"][:].astype("f8"), np.nan))
c = np.concatenate(c)                                             # (348, 192, 288)
clat = np.asarray(d["lat"][:]); clon = np.asarray(d["lon"][:])
ii = np.abs(clat[:, None] - lat[None, :]).argmin(0)
jj = np.abs(((clon[:, None] - (lon[None, :] % 360) + 180) % 360) - 180).argmin(0)
clm = c[:, ii][:, :, jj]
clm = np.where(clm > 1e30, np.nan, clm)
ok = np.isfinite(mod).all(0) & np.isfinite(obs).all(0) & np.isfinite(clm).all(0)
W = np.cos(np.radians(lat))[:, None] * np.ones(lon.size)


def daily(mon, pdec, njan):
    return np.interp(DOY, np.concatenate([[MID[-1] - 365], MID, [MID[0] + 365]]), np.concatenate([[pdec], mon, [njan]]))


def sos_eos(cv, thr=0.5):
    lo, hi = cv.min(), cv.max(); t = lo + thr * (hi - lo); ip = int(cv.argmax())
    up = np.where((cv[:-1] < t) & (cv[1:] >= t))[0]; up = up[up < ip]
    dn = np.where((cv[:-1] >= t) & (cv[1:] < t))[0]; dn = dn[dn >= ip]
    s = DOY[up[-1]] + (t - cv[up[-1]]) / (cv[up[-1] + 1] - cv[up[-1]]) if up.size else np.nan
    e = DOY[dn[0]] + (cv[dn[0]] - t) / (cv[dn[0]] - cv[dn[0] + 1]) if dn.size else np.nan
    return s, e


with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    ar6 = regionmask.defined_regions.ar6.land
    m3 = ar6.mask_3D(lon, lat)
out = ["GIMMS vs LM4+ vs CLM5 (BGC offline), %d-%d, regional mean over common valid cells; SOS/EOS = 50 %% amplitude per year, mean +- sd" % (Y0, Y1),
       "CLM5 leaf-off = day length < 10.92 h after the summer solstice; LM4+ = smoothed canopy T < 5/10 C", ""]
fig, axs = plt.subplots(2, 2, figsize=(10.5, 7.2), sharex=True)
for k, (name, ab) in enumerate(REG):
    r = ok & m3.sel(region=ar6.map_keys(ab)).values.astype(bool); w = W * r
    curves = {}; res = {}
    for key, v in (("GIMMS", obs), ("LM4+", mod), ("CLM5", clm)):
        reg = np.array([np.nansum(v[t] * w) / w.sum() for t in range(NY * 12)]).reshape(NY, 12)
        se = []
        for y in range(NY):
            pd = reg[y - 1, 11] if y > 0 else reg[y, 11]; nj = reg[y + 1, 0] if y < NY - 1 else reg[y, 0]
            se.append(sos_eos(daily(reg[y], pd, nj)))
        se = np.array(se); res[key] = se; curves[key] = reg.mean(0)
    line = "%-28s (%4d cells)" % (name, r.sum())
    for key in ("GIMMS", "LM4+", "CLM5"):
        s, e = res[key][:, 0], res[key][:, 1]
        line += " | %s SOS %5.1f EOS %5.1f" % (key, np.nanmean(s), np.nanmean(e))
    for key in ("LM4+", "CLM5"):
        line += " | d%s SOS %+5.1f EOS %+5.1f" % (key, np.nanmean(res[key][:, 0] - res["GIMMS"][:, 0]), np.nanmean(res[key][:, 1] - res["GIMMS"][:, 1]))
    out.append(line); print(line)
    if k < 4:
        ax = axs.ravel()[k]
        for key, col, ls in (("GIMMS", "0.55", "-"), ("LM4+", "tab:red", "-"), ("CLM5", "tab:blue", "--")):
            ax.plot(np.arange(1, 13), curves[key], color=col, ls=ls, lw=2.4, marker="o", ms=3, label=key)
            ax.axvline(1 + (np.nanmean(res[key][:, 1]) - 15.5) / 30.4, color=col, ls=":", lw=1.2)
        ax.set_title(name, loc="left", fontsize=11); ax.set_xticks(range(1, 13)); ax.set_xticklabels(list("JFMAMJJASOND")); ax.grid(alpha=0.3)
for ax in axs[:, 0]:
    ax.set_ylabel("LAI (m$^2$ m$^{-2}$)")
axs[0, 0].legend(loc="upper left", fontsize=9, frameon=False)
fig.tight_layout(); fig.savefig("../figures/fig_clm5_lm4_gimms_regions.png", dpi=200)
open("../data/clm5_lm4_gimms_sos_eos.txt", "w").write("\n".join(out) + "\n")
print("wrote figure and table")
