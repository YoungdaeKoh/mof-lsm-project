#!/usr/bin/env python3
"""Offline emulation: autumn canopy decline driven by the Delpierre et al. (2009, AFM 149:938) senescence state.

DM model: once day length P < Pstart (shortening), daily rate R = [Tb - T]^x * (P/Pstart)^y for T < Tb (else 0),
state S = sum R; colouring when S >= Ycrit. Published DBF set: Pstart 12.5 h, Tb 28.5 C, x = 2, y = 2, Ycrit 8268.
Here S is turned into a canopy fraction F = max(0, 1 - S/Ycrit), so the daily leaf loss scales with (Tb - T)^x
("decline as a function of falling temperature") instead of LM4's fixed 7.5 %/d after the switch.
LAI_new(t) = Lmin + (Lref(t) - Lmin) F(t), Lref = dayl_d daily LAI with its own switch drop removed (held at the
value before the switch), Lmin = dayl_d December mean (evergreen / winter floor). T = daily mean 2 m air
(t_ref_max + t_ref_min)/2 (vegn_temp_* are corrupt). Ycrit is either the published 8268 or calibrated so that the
50-70N median EOS50 bias vs GLASS 2010 is 0. Temperature sensitivity: rerun with T + 1 K (d/K, median of cells).
Effective loss rate = median daily % loss between 90 % and 10 % of the autumn amplitude.
Cells: rule species >= 50 % of CTRL July leaf area, GLASS amplitude >= 0.5, model LAI range > 0.3 (as
senescence_emulate_offline.py). Obs: GLASS 2010 daily (1-deg box of each C96 centre).
output: ../data/senescence_dm_offline_2010.txt
"""
import glob
import datetime as dt
import shapely
import numpy as np
import netCDF4 as nc
import regionmask

R = "/Volumes/data02/LM4P/cases/phentest_2010/dayl_d/"
P = "/Volumes/data01/MOF_LSM_project/poster/2026_LM4p_LAI/data/"
G = "/Volumes/data01/MOF_LSM_project/paper/2026_LM4p_phenology/data/obs_native/glass_1deg_2001_2015.nc"
DOY = np.arange(1, 366)

lai, tx, tn, lat, lon = [], [], [], [], []
for f in sorted(glob.glob(R + "20100101.land_daily.tile*.nc")):
    with nc.Dataset(f) as A:
        A.set_auto_mask(False)
        lai.append(A["lai"][:].astype("f8").reshape(365, -1))
        tx.append(A["t_ref_max"][:].astype("f8").reshape(365, -1)); tn.append(A["t_ref_min"][:].astype("f8").reshape(365, -1))
        lat.append(A["geolat_t"][:].ravel()); lon.append(A["geolon_t"][:].ravel())
lai = np.concatenate(lai, 1); T = (np.concatenate(tx, 1) + np.concatenate(tn, 1)) / 2 - 273.15
lat = np.concatenate(lat); lon = np.concatenate(lon); lon = np.where(lon > 180, lon - 360, lon)
z = np.load(P + "base_species_share_july2010_c96.npz", allow_pickle=True); assert np.allclose(z["lat"], lat)
sp = list(z["species"]); rule = sum(z["share"][sp.index(s)] for s in ("larix", "acer", "c3grass"))

with nc.Dataset(G) as A:
    t = A["time"][:].astype(float); x = np.ma.filled(A["lai"][:].astype("f8"), np.nan)
x[np.abs(x) > 100] = np.nan
day = [dt.date(2001, 1, 1) + dt.timedelta(int(v)) for v in t]
sel = np.array([d.year == 2010 for d in day]); dd = np.array([d.timetuple().tm_yday for d in day])[sel]
ci = np.clip(((lat + 90) // 1).astype(int), 0, 179); cj = np.clip(((lon + 180) // 1).astype(int), 0, 359)
xs = x[sel][:, ci, cj]
obs = np.array([np.interp(DOY, np.r_[dd[-1] - 365, dd, dd[0] + 365], np.r_[xs[-1, n], xs[:, n], xs[0, n]]) for n in range(lat.size)]).T
ok = np.all((lai >= 0) & (lai < 1e10), 0) & np.isfinite(obs).all(0) & (rule >= 0.5) & (lat >= 40) & (lat < 70) \
     & (obs.max(0) - obs.min(0) >= 0.5) & (lai.max(0) - lai.min(0) > 0.3) & np.all(np.abs(T) < 80, 0)
lai, T, obs, lat, lon = lai[:, ok], T[:, ok], obs[:, ok], lat[ok], lon[ok]

decl = np.radians(23.44) * np.sin(2 * np.pi * (284 + DOY) / 365)
Pday = 24 / np.pi * np.arccos(np.clip(-np.tan(np.radians(lat))[None, :] * np.tan(decl)[:, None], -1, 1))
short = (np.radians(lat)[None, :] * np.cos(2 * np.pi * (284 + DOY) / 365)[:, None]) < 0
ip = lai.argmax(0)
drop = np.zeros_like(lai, bool); drop[1:] = lai[1:] < 0.97 * lai[:-1]; drop &= np.arange(365)[:, None] > ip[None, :]
tsw = np.where(drop.any(0), drop.argmax(0), 364)
Lref = lai.copy()
for n in range(lai.shape[1]):
    Lref[tsw[n]:, n] = lai[max(tsw[n] - 1, 0), n]
Lmin = lai[334:365].mean(0)


def eos50(c):
    k = c.argmax(0); thr = c.min(0) + 0.5 * (c.max(0) - c.min(0))
    b = (c < thr[None, :]) & (np.arange(365)[:, None] > k[None, :])
    return np.where(b.any(0), b.argmax(0) + 1.0, np.nan)


def state(pstart, tb, xx, yy, dT=0.0):
    ps = pstart if np.ndim(pstart) else np.full(lat.size, pstart)
    on = short & (Pday < ps[None, :]); on[:172] = False
    Tm = T + dT
    r = np.where(on & (Tm < tb), np.maximum(tb - Tm, 0) ** xx * (Pday / ps[None, :]) ** yy, 0.0)
    return np.cumsum(r, 0)


def canopy(S, ycrit):
    return Lmin[None, :] + (Lref - Lmin[None, :]) * np.clip(1 - S / ycrit, 0, 1)


eo = eos50(obs); band = (lat >= 50) & (lat < 70)


def calibrate(S):
    lo, hi = 1.0, 1e7                                   # bisection on log Ycrit: median EOS50 bias (50-70N) = 0
    for _ in range(50):
        mid = np.sqrt(lo * hi); b = np.nanmedian((eos50(canopy(S, mid)) - eo)[band])
        lo, hi = (mid, hi) if b < 0 else (lo, mid)
    return np.sqrt(lo * hi)


def loss_rate(c):
    """median daily % loss between 90 % and 10 % of the autumn amplitude"""
    k = c.argmax(0); lo_ = c.min(0); amp = c.max(0) - lo_; out = np.full(c.shape[1], np.nan)
    for n in range(c.shape[1]):
        seg = c[k[n]:, n]
        i9 = np.argmax(seg <= lo_[n] + 0.9 * amp[n]); i1 = np.argmax(seg <= lo_[n] + 0.1 * amp[n])
        if i1 > i9:
            out[n] = 100 * (1 - (seg[i1] / seg[i9]) ** (1.0 / (i1 - i9)))
    return out


onset_lat = 13.5 + 0.19 * (np.abs(lat) - 45)
CASES = [("DM-DBF published", 12.5, 28.5, 2, 2, 8268.0), ("DM-DBF, Ycrit cal.", 12.5, 28.5, 2, 2, None),
         ("DM x=1, Ycrit cal.", 12.5, 28.5, 1, 2, None), ("DM x=0 (no T), cal.", 12.5, 28.5, 0, 2, None),
         ("DM onset lat, x=2, cal.", onset_lat, 28.5, 2, 2, None), ("DM onset lat, x=1, cal.", onset_lat, 28.5, 1, 2, None),
         ("DM onset lat, x=0 (no T), cal.", onset_lat, 28.5, 0, 2, None)]
ar6 = regionmask.defined_regions.ar6.land
GROUPS = [("50-70N", band), ("40-50N", (lat >= 40) & (lat < 50))] + [(c, shapely.contains_xy(ar6[c].polygon, lon, lat)) for c in ("ESB", "NWN", "RFE", "ENA")]
res = {"dayl_d (7.5 %/d switch)": (lai, None, np.nan)}
for name, ps, tb, xx, yy, yc in CASES:
    S = state(ps, tb, xx, yy); yc = yc if yc else calibrate(S)
    c = canopy(S, yc); c1 = canopy(state(ps, tb, xx, yy, 1.0), yc)
    res["%s Y=%.0f" % (name, yc)] = (c, c1, None)
out = ["Delpierre-type canopy decline on dayl_d 2010 (medians over %d C96 cells; bias = model - GLASS 2010)" % lat.size]
for gname, m in GROUPS:
    if m.sum() < 15:
        continue
    out += ["", "%s (n %d): obs Aug LAI %.2f, Sep LAI %.2f, EOS50 %.0f" % (gname, m.sum(), np.median(obs[212:243, m].mean(0)),
            np.median(obs[243:273, m].mean(0)), np.nanmedian(eo[m])),
            "  %-34s %7s %7s %7s %8s %8s" % ("case", "dAugLAI", "dSepLAI", "dEOS50", "loss%/d", "dEOS/dT")]
    for cname, (c, c1, _) in res.items():
        e = eos50(c[:, m]); sens = np.nanmedian(eos50(c1[:, m]) - e) if c1 is not None else np.nan
        out.append("  %-34s %+7.2f %+7.2f %+7.1f %8.1f %+8.2f" % (cname, np.median(c[212:243, m].mean(0) - obs[212:243, m].mean(0)),
                   np.median(c[243:273, m].mean(0) - obs[243:273, m].mean(0)), np.nanmedian(e - eo[m]), np.nanmedian(loss_rate(c[:, m])), sens))
obsrate = np.nanmedian(loss_rate(obs[:, band]))
out += ["", "obs GLASS 2010 50-70N loss%%/d (90->10 %%) median %.1f" % obsrate]
open("../data/senescence_dm_offline_2010.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
