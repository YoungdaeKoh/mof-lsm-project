#!/usr/bin/env python3
"""Observed SOS / EOS / LOS against latitude: are they tied to the equinoxes (12 h everywhere) or to temperature?

GIMMS LAI4g 1982-2010 monthly climatology (as s2 / p6), cells north of 20N with amplitude >= 0.5, SOS / EOS = 50 %
amplitude crossings (monthly means interpolated to days), LOS = EOS - SOS. Day length at each date from the cell's
latitude (Cooper declination + sunrise equation, as the model patch).
Reading: if phenology followed the equinoxes, SOS ~ doy 79 and EOS ~ doy 265 at every latitude (day length 12 h);
if it followed a fixed photoperiod, the day length at the event would be the same at every latitude;
if it followed temperature, the date would shift steadily with latitude and the day length at the event would not be fixed.
Per 5-degree band 25-70N: cos-lat weighted median dates and day lengths; least-squares slopes against latitude.
output: ../data/s6_obs_sos_eos_daylength_lat.txt
"""
import numpy as np
import netCDF4 as nc

D = np.arange(1, 366.0)
MID = np.array([15.5, 45, 74.5, 105, 135.5, 166, 196.5, 227.5, 258, 288.5, 319, 349.5])
g = nc.Dataset("../../../poster/2026_LM4p_LAI/data/gimms_lai_clim_1982_2010.nc")
clim = np.ma.filled(g["clim"][:].astype("f8"), np.nan)
lat = np.asarray(g["lat"][:]); lon = np.asarray(g["lon"][:])
ok = np.isfinite(clim).all(0) & (lat[:, None] > 20) & ((clim.max(0) - clim.min(0)) >= 0.5)


def daylen(doy, la):
    decl = np.radians(23.44) * np.sin(2 * np.pi * (284 + doy) / 365)
    return 24 / np.pi * np.arccos(np.clip(-np.tan(np.radians(la)) * np.tan(decl), -1, 1))


S, E = np.full(ok.shape, np.nan), np.full(ok.shape, np.nan)
for i, j in zip(*np.where(ok)):
    m = clim[:, i, j]
    c = np.interp(D, np.r_[MID[-1] - 365, MID, MID[0] + 365], np.r_[m[-1], m, m[0]])
    thr = c.min() + 0.5 * (c.max() - c.min()); ip = int(c.argmax())
    up = [k for k in range(ip) if c[k] < thr <= c[k + 1]]
    dn = [k for k in range(ip, 364) if c[k] >= thr > c[k + 1]]
    if up and dn:
        S[i, j] = D[up[-1]] + (thr - c[up[-1]]) / (c[up[-1] + 1] - c[up[-1]])
        E[i, j] = D[dn[0]] + (c[dn[0]] - thr) / (c[dn[0]] - c[dn[0] + 1])
LA = lat[:, None] * np.ones((1, lon.size))
v = np.isfinite(S) & np.isfinite(E) & (LA >= 25) & (LA < 70)
la, s, e = LA[v], S[v], E[v]; w = np.cos(np.radians(la))
ds, de = daylen(s, la), daylen(e, la)


def wmed(x, ww):
    o = np.argsort(x); c = np.cumsum(ww[o]); return x[o][np.searchsorted(c, 0.5 * c[-1])]


out = ["Observed (GIMMS 1982-2010 clim) SOS / EOS / LOS by latitude; equinoxes = doy 79 (Mar 20) and doy 265 (Sep 22), 12 h",
       "%-7s %5s | %5s %6s | %5s %6s | %5s | %6s" % ("band", "cells", "SOS", "dl_SOS", "EOS", "dl_EOS", "LOS", "SOS<79%")]
for a in range(25, 70, 5):
    m = (la >= a) & (la < a + 5)
    out.append("%-7s %5d | %5.0f %6.1f | %5.0f %6.1f | %5.0f | %6.1f" % (
        "%d-%dN" % (a, a + 5), m.sum(), wmed(s[m], w[m]), wmed(ds[m], w[m]), wmed(e[m], w[m]), wmed(de[m], w[m]),
        wmed(e[m] - s[m], w[m]), 100 * w[m][s[m] < 79].sum() / w[m].sum()))
sl = lambda y: np.polyfit(la, y, 1, w=np.sqrt(w))[0]
out += ["", "Weighted least-squares slope against latitude (25-70N, n %d cells):" % v.sum(),
        "  SOS %+.2f d/deg   EOS %+.2f d/deg   LOS %+.2f d/deg" % (sl(s), sl(e), sl(e - s)),
        "  day length at SOS %+.3f h/deg   at EOS %+.3f h/deg" % (sl(ds), sl(de)),
        "  across-cell SD: SOS %.1f d, EOS %.1f d; day length at SOS %.2f h, at EOS %.2f h" % (s.std(), e.std(), ds.std(), de.std())]
open("../data/s6_obs_sos_eos_daylength_lat.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
