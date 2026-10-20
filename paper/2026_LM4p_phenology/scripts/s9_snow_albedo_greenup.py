#!/usr/bin/env python3
"""Spring order snow-off -> albedo drop -> green-up, observations vs LM4p (dayl_d), 2010, by evergreen-conifer share.

Question: in conifer-rich boreal cells, is the satellite spring "green-up" partly the snow disappearing from an
evergreen canopy (so obs SOS tracks snow-off and the model's late-spring bias is partly an obs artefact)?
Obs (all 8-day, 1 deg, NH; grid checks in findings 2026-10-20): MOD10C2 snow cover %, GLASS02B03 shortwave albedo,
GLASS LAI (2010). Each series linearly interpolated to days over its valid 8-day values (mid-period dates).
  snow-off  = 1 + last day before doy 200 with snow cover >= 50 %
  albedo    = day the spring albedo falls through 50 % of (Feb-Apr max - Jun-Aug min), first crossing after the max
  SOS10/50  = day LAI first rises through 10 / 50 % of the annual amplitude before the peak
Model: dayl_d daily LAI and snow_soil (C96, binned to 1 deg); snow-off = 1 + last day before doy 200 with
snow_soil >= 5 kg m-2; SOS as obs. Evergreen share: CLM5 surfdata 2000 PFT 1-2 (needleleaf evergreen) of vegetated area.
Cells: 45-75N, GLASS LAI amplitude >= 0.5, all dates found. Medians.
output: ../data/s9_snow_albedo_greenup.txt
"""
import glob
import datetime as dt
import numpy as np
import netCDF4 as nc

D = np.arange(1, 366)
lat = 0.5 + np.arange(90); lon = -179.5 + np.arange(360)
with nc.Dataset("/Volumes/data02/MODIS/MOD10C2/mod10c2_snowcover_1deg_2010.nc") as A:
    sdoy = A["doy"][:] + 3.5; snow = np.ma.filled(A["snow"][:], np.nan)
with nc.Dataset("/Volumes/data02/GLASS_albedo/glass_albedo_sw_1deg_2010.nc") as A:
    adoy = A["doy"][:] + 3.5; alb = np.ma.filled(A["albedo"][:], np.nan)
with nc.Dataset("../data/obs_native/glass_1deg_2001_2015.nc") as A:
    t = A["time"][:].astype(float); x = np.ma.filled(A["lai"][:].astype("f8"), np.nan)
    assert np.isclose(A["lat"][0], -89.5) and np.isclose(A["lon"][0], -179.5)
day = [dt.date(2001, 1, 1) + dt.timedelta(int(v)) for v in t]
sel = np.array([d.year == 2010 for d in day]); ldoy = np.array([d.timetuple().tm_yday for d in day])[sel] + 3.5
lai = x[sel][:, 90:]; lai[np.abs(lai) > 100] = np.nan                       # NH rows, lat 0.5 .. 89.5


def daily(tt, v):
    """(n, 90, 360) 8-day -> (365, 90, 360) by linear interpolation over finite values; NaN if < 20 valid."""
    out = np.full((365, 90, 360), np.nan)
    for i in range(45, 76):
        for j in range(360):
            y = v[:, i, j]; m = np.isfinite(y)
            if m.sum() >= 20:
                out[:, i, j] = np.interp(D, tt[m], y[m])
    return out


S, A_, L = daily(sdoy, snow), daily(adoy, alb), daily(ldoy, lai)


def snow_off(s, thr):
    b = (s[:199] >= thr)
    last = np.where(b.any(0), 198 - np.argmax(b[::-1], 0), -1)
    return np.where(b.any(0), last + 2.0, np.nan)


def alb_drop(a):
    mx = np.nanmax(a[31:120], 0); kmx = 31 + np.nanargmax(np.where(np.isfinite(a[31:120]), a[31:120], -1), 0)
    mn = np.nanmin(a[151:243], 0); thr = mn + 0.5 * (mx - mn)
    b = (a < thr[None]) & (np.arange(365)[:, None, None] > kmx[None])
    return np.where(b.any(0) & (mx - mn > 0.05), b.argmax(0) + 1.0, np.nan)


def sos(c, f):
    pk = c.argmax(0); thr = np.nanmin(c[:200], 0) + f * (np.nanmax(c, 0) - np.nanmin(c[:200], 0))
    b = (c >= thr[None]) & (np.arange(365)[:, None, None] <= pk[None])
    return np.where(b.any(0), b.argmax(0) + 1.0, np.nan)


so, ad = snow_off(S, 50.0), alb_drop(A_)
s10, s50 = sos(L, 0.1), sos(L, 0.5)

# model dayl_d, C96 -> 1 deg
num_l = np.zeros((365, 90, 360)); num_s = np.zeros((365, 90, 360)); den = np.zeros((90, 360))
for f in sorted(glob.glob("/Volumes/data02/LM4P/cases/phentest_2010/dayl_d/20100101.land_daily.tile*.nc")):
    with nc.Dataset(f) as B:
        B.set_auto_mask(False)
        la = B["geolat_t"][:].ravel(); lo = B["geolon_t"][:].ravel(); lo = np.where(lo > 180, lo - 360, lo)
        v = B["lai"][:].astype("f8").reshape(365, -1); sw = B["snow_soil"][:].astype("f8").reshape(365, -1)
    ok = (la >= 0) & np.all((v >= 0) & (v < 1e10), 0) & np.all(np.abs(sw) < 1e10, 0)
    ci = ((la[ok]) // 1).astype(int); cj = np.clip(((lo[ok] + 180) // 1).astype(int), 0, 359)
    np.add.at(den, (ci, cj), 1.0)
    for k in range(365):
        np.add.at(num_l[k], (ci, cj), v[k, ok]); np.add.at(num_s[k], (ci, cj), sw[k, ok])
ML = np.where(den > 0, num_l / np.maximum(den, 1), np.nan); MS = np.where(den > 0, num_s / np.maximum(den, 1), np.nan)
mso, m50, m10 = snow_off(MS, 5.0), sos(ML, 0.5), sos(ML, 0.1)

with nc.Dataset("../../../poster/2026_LM4p_LAI/data/clm5_surfdata_pft_0.9x1.25_simyr2000.nc") as g:
    pft = np.ma.filled(g["pct_pft"][:].astype("f8"), 0); crop = np.ma.filled(g["pct_crop"][:].astype("f8"), 0)
    clat = np.asarray(g["lat"][:]); clon = np.asarray(g["lon"][:])
net = (pft[1] + pft[2]) / np.maximum(pft[1:].sum(0) + crop, 1e-6)
ii = np.abs(clat[:, None] - lat[None, :]).argmin(0); jj = np.abs(((clon[:, None] - lon[None, :]) + 180) % 360 - 180).argmin(0)
NET = net[ii][:, jj]

LA = lat[:, None] * np.ones((1, 360))
amp = np.nanmax(L, 0) - np.nanmin(L, 0)
base = (LA >= 45) & (LA < 75) & (amp >= 0.5) & np.isfinite(so) & np.isfinite(ad) & np.isfinite(s50) & np.isfinite(s10)
out = ["Spring order 2010 (doy medians); NET = evergreen needleleaf share (CLM5); model = dayl_d",
       "%-18s %5s | %6s %6s %6s %6s | %8s %8s %9s | %6s %6s %8s" % ("group", "cells", "snowof", "albdrp", "SOS10", "SOS50", "S10-snow",
       "S50-snow", "|S10-sn|<8", "Msnow", "MSOS50", "M-O SOS50")]
for gname, g in [("45-55N", (LA >= 45) & (LA < 55)), ("55-65N", (LA >= 55) & (LA < 65)), ("65-75N", (LA >= 65) & (LA < 75))] + \
                [("NET < 20 %", NET < 0.2), ("NET 20-50 %", (NET >= 0.2) & (NET < 0.5)), ("NET >= 50 %", NET >= 0.5)] + \
                [("50-70N NET<20%", (LA >= 50) & (LA < 70) & (NET < 0.2)), ("50-70N NET>=50%", (LA >= 50) & (LA < 70) & (NET >= 0.5))]:
    m = base & g
    if m.sum() < 15:
        continue
    mm = m & np.isfinite(m50) & np.isfinite(mso)
    out.append("%-18s %5d | %6.0f %6.0f %6.0f %6.0f | %+8.0f %+8.0f %8.0f%% | %6.0f %6.0f %+8.0f" % (
        gname, m.sum(), np.median(so[m]), np.median(ad[m]), np.median(s10[m]), np.median(s50[m]), np.median((s10 - so)[m]),
        np.median((s50 - so)[m]), 100 * np.mean(np.abs(s10 - so)[m] < 8), np.median(mso[mm]), np.median(m50[mm]), np.median((m50 - s50)[mm])))
r = lambda a, b, m: np.corrcoef(a[m], b[m])[0, 1]
m = base & (LA >= 50) & (LA < 70)
out += ["", "50-70N cell correlations (n %d): r(SOS10, snow-off) %.2f, r(SOS50, snow-off) %.2f, r(albedo drop, snow-off) %.2f" % (
    m.sum(), r(s10, so, m), r(s50, so, m), r(ad, so, m))]
open("../data/s9_snow_albedo_greenup.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
