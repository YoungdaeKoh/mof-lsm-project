#!/usr/bin/env python3
"""Offline emulation of a gradual autumn senescence (Birch-style onset + slow leaf loss) on top of dayl_d (DL13/12).

Model: dayl_d 2010 daily LAI per C96 cell. Switch day t_sw = first day after the annual peak with a day-over-day
LAI drop > 3 % (the existing leaf-off rule: trees 7.5 %/d, grass immediate). Emulated senescence:
  onset t0 = first shortening day with day length < dl_sen(lat) = 13.5 + 0.19 (|lat| - 45) h
             (onset day length of GLASS declines, s4_senescence_shape.py: 13.5 / 15.2 / 17.3 h at 45 / 55 / 65N)
  LAI_new(t) = LAI(t) * exp(-k (min(t, t_sw) - t0)) for t >= t0 (slow loss before the switch, the switch then
  removes the rest from the reduced level); growth assumed not to refill the lost leaves.
GPP: monthly gpp of dayl_d scaled by the fAPAR ratio, fAPAR = 1 - exp(-0.5 LAI) (Sep-Oct GPP followed fAPAR within
2 %, gpp_vs_fapar_dl.py). Obs: GLASS 2010 8-day -> daily (1-deg box holding the C96 centre), FLUXCOM-X GPP 2010.
Metrics per group: Aug and Sep mean LAI bias, 50 % EOS bias (daily curves, peak-to-minimum amplitude), Aug GPP bias.
Cells: rule species (larix + acer + c3grass) >= 50 % of CTRL July leaf area, 40-70N, GLASS amplitude >= 0.5,
model LAI range > 0.3. Plain medians over C96 cells.
output: ../data/senescence_emulate_offline_2010.txt
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
KS = (0.01, 0.02, 0.03)
MON = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])      # month m = days MON[m]..MON[m+1]-1 (0-based)

lai, gpp, lat, lon = [], [], [], []
for f in sorted(glob.glob(R + "20100101.land_daily.tile*.nc")):
    fm = f.replace("land_daily", "land_month")
    with nc.Dataset(f) as A, nc.Dataset(fm) as B:
        A.set_auto_mask(False); B.set_auto_mask(False)
        lai.append(A["lai"][:].astype("f8").reshape(365, -1)); gpp.append(B["gpp"][:].astype("f8").reshape(12, -1))
        lat.append(A["geolat_t"][:].ravel()); lon.append(A["geolon_t"][:].ravel())
lai = np.concatenate(lai, 1); gpp = np.concatenate(gpp, 1) * 1000.0 / 365.0      # kg C m-2 yr-1 -> g C m-2 d-1
lat = np.concatenate(lat); lon = np.concatenate(lon); lon = np.where(lon > 180, lon - 360, lon)
z = np.load(P + "base_species_share_july2010_c96.npz", allow_pickle=True)
assert np.allclose(z["lat"], lat)
sp = list(z["species"]); rule = sum(z["share"][sp.index(s)] for s in ("larix", "acer", "c3grass"))

# GLASS 2010 daily at the 1-deg box of each C96 centre
with nc.Dataset(G) as A:
    t = A["time"][:].astype(float); x = np.ma.filled(A["lai"][:].astype("f8"), np.nan); assert np.isclose(A["lat"][0], -89.5)
x[np.abs(x) > 100] = np.nan
day = [dt.date(2001, 1, 1) + dt.timedelta(int(v)) for v in t]
sel = np.array([d.year == 2010 for d in day]); dd = np.array([d.timetuple().tm_yday for d in day])[sel]
ci = np.clip(((lat + 90) // 1).astype(int), 0, 179); cj = np.clip(((lon + 180) // 1).astype(int), 0, 359)
xs = x[sel][:, ci, cj]                                                              # (n8day, cells)
obs = np.array([np.interp(DOY, np.r_[dd[-1] - 365, dd, dd[0] + 365], np.r_[xs[-1, n], xs[:, n], xs[0, n]])
                for n in range(lat.size)]).T
with nc.Dataset(P + "fluxcomx_gpp_monthly_1deg_2001_2021.nc") as A:
    assert np.isclose(A["lat"][0], -89.5) and np.isclose(A["lon"][0], -179.5)
    fx = np.ma.filled(A["gpp"][(2010 - 2001) * 12 + 7].astype("f8"), np.nan)[ci, cj]  # Aug 2010

ok = np.all((lai >= 0) & (lai < 1e10), 0) & np.isfinite(obs).all(0) & (rule >= 0.5) & (lat >= 40) & (lat < 70) \
     & (obs.max(0) - obs.min(0) >= 0.5) & (lai.max(0) - lai.min(0) > 0.3) & np.isfinite(gpp).all(0)

decl = np.radians(23.44) * np.sin(2 * np.pi * (284 + DOY) / 365)
dayl = 24 / np.pi * np.arccos(np.clip(-np.tan(np.radians(lat))[None, :] * np.tan(decl)[:, None], -1, 1))
short = (np.radians(lat)[None, :] * np.cos(2 * np.pi * (284 + DOY) / 365)[:, None]) < 0
on = short & (dayl < (13.5 + 0.19 * (np.abs(lat) - 45))[None, :]); on[:172] = False
t0 = np.where(on.any(0), on.argmax(0), 364)
ip = lai.argmax(0)
drop = np.zeros_like(lai, bool); drop[1:] = lai[1:] < 0.97 * lai[:-1]
drop &= np.arange(365)[:, None] > ip[None, :]
tsw = np.where(drop.any(0), drop.argmax(0), 364)


def eos50(c):
    """50 % EOS (doy) of daily curves (365, n): first day after the peak below min + 0.5 amplitude."""
    k = c.argmax(0); thr = c.min(0) + 0.5 * (c.max(0) - c.min(0))
    b = (c < thr[None, :]) & (np.arange(365)[:, None] > k[None, :])
    return np.where(b.any(0), b.argmax(0) + 1.0, np.nan)


fap = lambda L: 1 - np.exp(-0.5 * L)
T = np.arange(365)[:, None]
cases = {"dayl_d": lai}
for k in KS:
    S = np.exp(-k * np.clip(np.minimum(T, tsw[None, :]) - t0[None, :], 0, None))
    cases["sen k=%.0f%%" % (100 * k)] = lai * S
eos_o = eos50(obs)

ar6 = regionmask.defined_regions.ar6.land
GROUPS = [("40-50N", (lat >= 40) & (lat < 50)), ("50-60N", (lat >= 50) & (lat < 60)), ("60-70N", (lat >= 60) & (lat < 70)),
          ("50-70N", (lat >= 50) & (lat < 70))] + [(c, shapely.contains_xy(ar6[c].polygon, lon, lat)) for c in ("ESB", "WSB", "NWN", "RFE", "ENA")]
out = ["Offline gradual-senescence emulation on dayl_d 2010 (medians over C96 cells; bias = model - obs)",
       "onset dl_sen = 13.5 + 0.19(|lat|-45) h; obs LAI = GLASS 2010 daily, obs GPP = FLUXCOM-X Aug 2010 (g C m-2 d-1)"]
for name, g in GROUPS:
    m = ok & g
    if m.sum() < 15:
        continue
    out += ["", "%s  n %d  onset doy %d, switch doy %d (medians); obs Aug LAI %.2f, Sep LAI %.2f, EOS50 %.0f, Aug GPP %.2f" % (
        name, m.sum(), np.median(t0[m]) + 1, np.median(tsw[m]) + 1, np.median(obs[212:243, m].mean(0)),
        np.median(obs[243:273, m].mean(0)), np.nanmedian(eos_o[m]), np.nanmedian(fx[m])),
        "  %-10s %8s %8s %8s %9s %9s" % ("case", "dAugLAI", "dSepLAI", "dEOS50", "dAugGPP", "AugGPP%")]
    for cname, c in cases.items():
        ag = gpp[7, m] * fap(c[212:243, m]).mean(0) / np.maximum(fap(lai[212:243, m]).mean(0), 1e-6)
        out.append("  %-10s %+8.2f %+8.2f %+8.1f %+9.2f %+9.1f" % (
            cname, np.median(c[212:243, m].mean(0) - obs[212:243, m].mean(0)), np.median(c[243:273, m].mean(0) - obs[243:273, m].mean(0)),
            np.nanmedian(eos50(c[:, m]) - eos_o[m]), np.nanmedian(ag - fx[m]), 100 * (np.median(ag) / np.median(gpp[7, m]) - 1)))
open("../data/senescence_emulate_offline_2010.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
