#!/usr/bin/env python3
"""Latitude-dependent autumn day-length threshold: fit the day length at observed EOS against latitude.

Per cell north of 25N (amplitude >= 0.5), EOS = 50 % amplitude crossing after the peak (monthly climatology
interpolated to days, as s2 / s6), day length at EOS from the cell's latitude (Cooper + sunrise equation).
Products: GIMMS LAI4g 1982-2010 climatology (main, as s2) and GLASS 2001-2015 climatology (check).
Fit: dl_crit = a + b (lat - 40) over 25-70N, (i) cos-lat weighted least squares on cells, (ii) on 5-degree band medians.
Residuals: median observed day length minus the fit, per AR6 region used in the paper + TIB.
output: ../data/s7_eos_daylength_lat_fit.txt
"""
import warnings
import numpy as np
import netCDF4 as nc
import regionmask

D = np.arange(1, 366.0)
MID = np.array([15.5, 45, 74.5, 105, 135.5, 166, 196.5, 227.5, 258, 288.5, 319, 349.5])
P = "../../../poster/2026_LM4p_LAI/data/"


def daylen(doy, la):
    decl = np.radians(23.44) * np.sin(2 * np.pi * (284 + doy) / 365)
    return 24 / np.pi * np.arccos(np.clip(-np.tan(np.radians(la)) * np.tan(decl), -1, 1))


def eos_dl(clim, lat):
    ok = np.isfinite(clim).all(0) & (lat[:, None] >= 25) & (lat[:, None] < 70) & ((clim.max(0) - clim.min(0)) >= 0.5)
    dl = np.full(ok.shape, np.nan)
    for i, j in zip(*np.where(ok)):
        m = clim[:, i, j]
        c = np.interp(D, np.r_[MID[-1] - 365, MID, MID[0] + 365], np.r_[m[-1], m, m[0]])
        thr = c.min() + 0.5 * (c.max() - c.min()); ip = int(c.argmax())
        dn = [k for k in range(ip, 364) if c[k] >= thr > c[k + 1]]
        if dn:
            k = dn[0]; dl[i, j] = daylen(D[k] + (c[k] - thr) / (c[k] - c[k + 1]), lat[i])
    return dl


with nc.Dataset(P + "gimms_lai_clim_1982_2010.nc") as g:
    gim = np.ma.filled(g["clim"][:].astype("f8"), np.nan); lat = np.asarray(g["lat"][:]); lon = np.asarray(g["lon"][:])
with nc.Dataset(P + "glass_lai_modis_monthly_1deg_2001_2020.nc") as g:
    x = np.ma.filled(g["lai"][:180].astype("f8"), np.nan)        # 2001-2015
    assert np.allclose(g["lat"][:], lat) and np.allclose(g["lon"][:], lon)
x[np.abs(x) > 100] = np.nan
gla = np.nanmean(x.reshape(15, 12, 180, 360), 0)
LA = lat[:, None] * np.ones((1, lon.size)); W = np.cos(np.radians(LA))
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    reg = regionmask.defined_regions.ar6.land.mask(lon, lat).values


# evergreen needleleaf share of vegetated area (CLM5 surfdata 2000, PFT 1-2; 0.9x1.25 -> nearest 1-deg cell); cells
# dominated by evergreen conifers carry the EOS of their understory / grass / birch, not of the deciduous canopy
with nc.Dataset(P + "clm5_surfdata_pft_0.9x1.25_simyr2000.nc") as g:
    pft = np.ma.filled(g["pct_pft"][:].astype("f8"), 0); crop = np.ma.filled(g["pct_crop"][:].astype("f8"), 0)
    clat = np.asarray(g["lat"][:]); clon = np.asarray(g["lon"][:])
net = (pft[1] + pft[2]) / np.maximum(pft[1:].sum(0) + crop, 1e-6)
ii = np.abs(clat[:, None] - lat[None, :]).argmin(0); jj = np.abs(((clon[:, None] - lon[None, :]) + 180) % 360 - 180).argmin(0)
NET = net[ii][:, jj]
EVG = 0.3   # cells with evergreen needleleaf >= 30 % of vegetated area left out in the second fit


def wmed(v, w):
    o = np.argsort(v); c = np.cumsum(w[o]); return v[o][np.searchsorted(c, 0.5 * c[-1])]


out = []
for name, clim, sel in (("GIMMS 1982-2010", gim, True), ("GLASS 2001-2015", gla, True),
                        ("GIMMS 1982-2010, evergreen needleleaf < 30 %", gim, NET < EVG),
                        ("GLASS 2001-2015, evergreen needleleaf < 30 %", gla, NET < EVG)):
    dl = eos_dl(clim, lat); v = np.isfinite(dl) & sel
    la, y, w = LA[v], dl[v], W[v]
    b1, a1 = np.polyfit(la - 40, y, 1, w=np.sqrt(w))
    bands = [(a, a + 5) for a in range(25, 70, 5)]
    bm = np.array([[(a + b) / 2, wmed(y[(la >= a) & (la < b)], w[(la >= a) & (la < b)])] for a, b in bands])
    b2, a2 = np.polyfit(bm[:, 0] - 40, bm[:, 1], 1)
    out += ["%s: %d cells" % (name, v.sum()),
            "  (i) cells       dl_crit = %.2f + %.4f (lat - 40)" % (a1, b1),
            "  (ii) band medians dl_crit = %.2f + %.4f (lat - 40)" % (a2, b2),
            "  band  " + " ".join("%5.1f" % c for c in bm[:, 0]),
            "  obs   " + " ".join("%5.2f" % c for c in bm[:, 1]),
            "  fit(ii)" + " ".join("%5.2f" % (a2 + b2 * (c - 40)) for c in bm[:, 0]),
            "  region  cells  lat  obs_med  fit(ii)  resid(h)"]
    for code in ("NWN", "ESB", "RFE", "WSB", "NEU", "NEN", "RAR", "ENA", "WCE", "EAS", "EEU", "TIB"):
        m = v & (reg == regionmask.defined_regions.ar6.land.map_keys(code))
        if m.sum() < 10:
            continue
        lm = wmed(LA[m], W[m]); om = wmed(dl[m], W[m]); f = np.median(a2 + b2 * (LA[m] - 40))
        out.append("  %-6s %5d %5.1f %7.2f %8.2f %+8.2f" % (code, m.sum(), lm, om, f, om - f))
    out.append("")
open("../data/s7_eos_daylength_lat_fit.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
