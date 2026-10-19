#!/usr/bin/env python3
"""Do the 2010 phenology pilot runs improve GPP and ET against observations?

Runs (one year, 2010, same 1 Jan 2010 CTRL state): base (CTRL), tc10, offon (DL14+TC10 = autumn-only TC10),
dayl (DL13/12), dayl2 (DLtype).  Model fields regridded with lm4p_to_latlon.py (1 deg, nearest C96 cell):
  gpp kg C m-2 yr-1 -> g C m-2 d-1 ; evap_land kg m-2 s-1 -> mm d-1 ; nep (no obs here, reported only).
Obs: FLUXCOM-X-BASE GPP (../data/fluxcomx_gpp_monthly_1deg_2001_2021.nc, g C m-2 d-1, 1 deg),
     GLEAM v4.2a E (0.5 deg NODE grid, lat -90..90 x lon 0..359.5, mm/month) -> 1 deg cell mean with
     trapezoid weights (0.25, 0.5, 0.25)^2 over the 3x3 nodes around each 1-deg centre, / days in month.
Both obs: year 2010 and the 2001-2020 climatology.
Regions: AR6 NEU, RFE, NWN, ESB (regionmask) and the 50-70N land band; cos-lat weights; common cells =
finite in every run and in the obs for all 12 months.
Grid checks 2026-10-12: GLEAM raw index plot = world map, lat ascending, lon 0-360; FLUXCOM-X 1 deg lat
ascending, lon -180..180 (scratchpad gc_*.png).
Output: ../data/phentest_flux_vs_obs_2010.txt (full tables); console = Sep-Oct summary only.
usage: FLUXDIR=<dir with *_case.{gpp,nep,evap_land}.2010-2010.1deg.nc> python3 p21_phentest_flux_vs_obs.py
"""
import os
import calendar
import numpy as np
import netCDF4 as nc
import regionmask

FLUXDIR = os.environ["FLUXDIR"]
RUNS = [("base", "base_case", "CTRL"), ("tc10", "tc10_case", "TC10"), ("offon", "offon_d_case", "DL14+TC10"),
        ("dayl", "dayl_d_case", "DL13/12"), ("dayl2", "dayl2_d_case", "DLtype")]
YEAR = 2010
lat = -89.5 + np.arange(180)
lon = -179.5 + np.arange(360)
ndays = np.array([calendar.monthrange(YEAR, m)[1] for m in range(1, 13)], float)


def model(case, var):
    with nc.Dataset("%s/%s.%s.%d-%d.1deg.nc" % (FLUXDIR, case, var, YEAR, YEAR)) as f:
        assert np.allclose(f["lat"][:], lat) and np.allclose(f["lon"][:], lon)
        a = np.ma.filled(f[var][:].astype(float), np.nan)
    a[np.abs(a) > 1e19] = np.nan
    return a * (1000.0 / 365.0 if var in ("gpp", "nep") else 86400.0)


def fluxcom():
    with nc.Dataset("../data/fluxcomx_gpp_monthly_1deg_2001_2021.nc") as f:
        assert np.allclose(f["lat"][:], lat) and np.allclose(f["lon"][:], lon)
        t = nc.num2date(f["time"][:], f["time"].units)
        a = np.ma.filled(f["gpp"][:].astype(float), np.nan)
    yr = np.array([x.year for x in t])
    y2010 = a[yr == YEAR]
    clim = np.stack([np.nanmean(a[(yr >= 2001) & (yr <= 2020)][m::12], 0) for m in range(12)])
    return y2010, clim


def fluxcom_nee():
    """FLUXCOM-X-BASE NEE 0.5 deg (lat DESCENDING 89.75..-89.75, lon -179.75..179.75, g C m-2 d-1,
    negative = uptake; grid-verify 2026-10-12) -> 1 deg nanmean of 2x2, lat ascending."""
    years = range(2001, 2021)
    out = {}
    for y in years:
        with nc.Dataset("/Volumes/data02/FLUXCOM_X_BASE/NEE_monthly_0.5deg/FLUXCOM-X-BASE_NEE_monthly_0.5deg_%d.nc" % y) as f:
            assert f["lat"][0] > 0 and f["lon"][0] < 0
            a = np.ma.filled(f["NEE"][:].astype(float), np.nan)[:, ::-1, :]
        out[y] = np.nanmean(a.reshape(12, 180, 2, 360, 2), axis=(2, 4))
    clim = np.nanmean(np.stack([out[y] for y in years]), 0)
    return out[YEAR], clim


def gleam():
    f = nc.Dataset("/Volumes/data02/GLEAM/v4.2a/monthly/GLEAM_v4.2a_E_1980_2023_0.5deg.nc")
    la, lo = f["latitude"][:], f["longitude"][:]
    assert la[0] == -90 and la[-1] == 90 and lo[0] == 0 and lo[-1] == 359.5
    t = nc.num2date(f["time"][:], f["time"].units, f["time"].calendar)
    yr = np.array([x.year for x in t]); mo = np.array([x.month for x in t])
    w1 = np.array([0.25, 0.5, 0.25])
    ilat = 2 * np.arange(180) + 1                                 # node index of each 1-deg centre (-89.5 -> 1)
    ilon = (2 * ((lon + 360) % 360)).astype(int)                  # node index of lon centre (x.5 deg)

    def to1deg(e):                                                # e (361, 720) mm/month
        out = np.zeros((180, 360)); wsum = np.zeros((180, 360))
        for di, wi in zip((-1, 0, 1), w1):
            for dj, wj in zip((-1, 0, 1), w1):
                v = e[ilat + di][:, (ilon + dj) % 720]
                ok = np.isfinite(v)
                out += np.where(ok, v, 0) * wi * wj; wsum += ok * wi * wj
        return np.where(wsum > 0.5, out / np.where(wsum > 0, wsum, 1), np.nan)

    def month(k):
        e = np.ma.filled(f["E"][k].astype(float), np.nan); e[np.abs(e) > 1e19] = np.nan
        return to1deg(e)

    y2010 = np.stack([month(np.where((yr == YEAR) & (mo == m))[0][0]) for m in range(1, 13)]) / ndays[:, None, None]
    clim = []
    for m in range(1, 13):
        ks = np.where((yr >= 2001) & (yr <= 2020) & (mo == m))[0]
        clim.append(np.nanmean([month(k) / calendar.monthrange(int(yr[k]), m)[1] for k in ks], 0))
    return y2010, np.stack(clim)


masks = {}
ar6 = regionmask.defined_regions.ar6.land
rm = ar6.mask(lon, lat)
for code in ("NEU", "RFE", "NWN", "ESB"):
    masks[code] = (rm.values == ar6.map_keys(code))
masks["50-70N"] = np.isfinite(rm.values) & ((lat >= 50) & (lat <= 70))[:, None]
W = np.cos(np.radians(lat))[:, None] * np.ones((1, 360))

obs = {"gpp": dict(zip(("2010", "clim"), fluxcom())), "evap_land": dict(zip(("2010", "clim"), gleam())),
       "nee": dict(zip(("2010", "clim"), fluxcom_nee()))}
mod = {v: {k: model(c, v) for k, c, _ in RUNS} for v in ("gpp", "nep", "evap_land")}
mod["nee"] = {k: -a for k, a in mod.pop("nep").items()}          # LM4 nep = -NEE (negative NEE = uptake)

SO, MJ = [8, 9], [4, 5]
lines, summ = ["Pilot runs 2010 vs obs (FLUXCOM-X GPP g C m-2 d-1, GLEAM E mm d-1; NEP g C m-2 d-1 model only)",
               "common cells = finite in all runs and obs (2010 and clim) for 12 months; cos-lat weights"], []
for var, oname in (("gpp", "FLUXCOM-X"), ("evap_land", "GLEAM"), ("nee", "FLUXCOM-X")):
    for reg, m in masks.items():
        ok = m.copy()
        for k in mod[var]:
            ok &= np.isfinite(mod[var][k]).all(0)
        if oname:
            ok &= np.isfinite(obs[var]["2010"]).all(0) & np.isfinite(obs[var]["clim"]).all(0)
        ww = W * ok
        avg = lambda a: np.array([np.nansum(a[i] * ww) / ww.sum() for i in range(12)])
        series = {k: avg(mod[var][k]) for k in mod[var]}
        if oname:
            series["obs2010"] = avg(obs[var]["2010"]); series["obsclim"] = avg(obs[var]["clim"])
        lines.append("\n%s  %s  (%d cells)" % (var, reg, ok.sum()))
        lines.append("  %-10s" % "month" + "".join("%7d" % i for i in range(1, 13)) + "   SepOct  MayJun  annual")
        for k, s in series.items():
            lines.append("  %-10s" % k + "".join("%7.2f" % x for x in s) +
                         "  %7.2f %7.2f %7.2f" % (s[SO].mean(), s[MJ].mean(), s.mean()))
        if oname:
            o = series["obs2010"]
            for k, _, lab in RUNS:
                s = series[k]
                lines.append("  %-10s bias SepOct %+6.2f MayJun %+6.2f annual %+6.2f | RMSE(12 mo) vs 2010 %5.2f vs clim %5.2f"
                             % (k, s[SO].mean() - o[SO].mean(), s[MJ].mean() - o[MJ].mean(), s.mean() - o.mean(),
                                np.sqrt(((s - o) ** 2).mean()), np.sqrt(((s - series["obsclim"]) ** 2).mean())))
            b0 = series["base"][SO].mean() - o[SO].mean()
            summ.append("%-9s %-6s obs2010 %.2f | " % (var, reg, o[SO].mean()) + " ".join(
                "%s %+.2f(%+.0f%%)" % (lab, series[k][SO].mean() - o[SO].mean(),
                                       100 * (1 - (series[k][SO].mean() - o[SO].mean()) / b0) if k != "base" else 0)
                for k, _, lab in RUNS))
        else:
            summ.append("%-9s %-6s SepOct " % (var, reg) + " ".join("%s %.2f" % (lab, series[k][SO].mean()) for k, _, lab in RUNS))

# --- surface soil moisture vs ESA CCI C3S v202505 COMBINED (0.25 deg, lat DESCENDING, m3 m-3; grid-verify 2026-10-12)
# model = soil_liq (kg m-3, liquid only) of layers 1-2 (centres 0.01/0.04 m -> 0-0.02/0.02-0.06 m), dz-weighted, /1000.
# CCI has no value over frozen/snow/dense-forest cells -> month-wise common cells (obs finite and model finite),
# a month is kept when >= 30 % of the region's cells are valid.
def ssm_model(case):
    with nc.Dataset("%s/%s.soil_liq.%d-%d.1deg.nc" % (FLUXDIR, case, YEAR, YEAR)) as f:
        z = f["zfull_soil"][:]
        assert abs(z[0] - 0.01) < 1e-6 and abs(z[1] - 0.04) < 1e-6
        a = np.ma.filled(f["soil_liq"][:, :2].astype(float), np.nan)
    a[np.abs(a) > 1e19] = np.nan
    return (a[:, 0] * 0.02 + a[:, 1] * 0.04) / 0.06 / 1000.0


def cci(y, m):
    fn = ("/Volumes/data02/SoilMoisture/ESACCI_C3S_v202505_monthly/surface_soil_moisture_volumetric/"
          "C3S-SOILMOISTURE-L3S-SSMV-COMBINED-MONTHLY-%d%02d01000000-TCDR-v202505.0.0.nc" % (y, m))
    with nc.Dataset(fn) as f:
        assert f["lat"][0] > 0 and f["lon"][0] < 0
        a = np.ma.filled(f["sm"][0].astype(float), np.nan)[::-1]
    a[a < 0] = np.nan
    blk = a.reshape(180, 4, 360, 4)
    n = np.isfinite(blk).sum(axis=(1, 3))
    return np.where(n >= 4, np.nanmean(blk, axis=(1, 3)), np.nan)          # >= 1/4 of the 0.25-deg cells valid


import warnings
warnings.simplefilter("ignore", RuntimeWarning)
ssm_obs = np.stack([cci(YEAR, m) for m in range(1, 13)])
ssm_clim = np.stack([np.nanmean([cci(y, m) for y in range(2001, 2021)], 0) for m in range(1, 13)])
ssm_mod = {k: ssm_model(c) for k, c, _ in RUNS}
for reg, m in masks.items():
    lines.append("\nssm (m3 m-3)  %s  month-wise common cells; n = valid cells per month" % reg)
    rows = {k: [] for k in list(ssm_mod) + ["obs2010", "obsclim", "n"]}
    for i in range(12):
        ok = m & np.isfinite(ssm_obs[i]) & np.isfinite(ssm_clim[i])
        for k in ssm_mod:
            ok &= np.isfinite(ssm_mod[k][i])
        if ok.sum() < 0.3 * m.sum():
            for k in rows:
                rows[k].append(np.nan)
            continue
        ww = W * ok
        for k in ssm_mod:
            rows[k].append(np.nansum(ssm_mod[k][i] * ww) / ww.sum())
        rows["obs2010"].append(np.nansum(ssm_obs[i] * ww) / ww.sum())
        rows["obsclim"].append(np.nansum(ssm_clim[i] * ww) / ww.sum())
        rows["n"].append(ok.sum())
    rows = {k: np.array(v, float) for k, v in rows.items()}
    lines.append("  %-10s" % "month" + "".join("%7d" % i for i in range(1, 13)) + "   SepOct  MayJun")
    for k, s in rows.items():
        fmt = "%7.0f" if k == "n" else "%7.3f"
        lines.append("  %-10s" % k + "".join(fmt % x if np.isfinite(x) else "      -" for x in s) +
                     ("" if k == "n" else "  %7.3f %7.3f" % (np.nanmean(s[SO]), np.nanmean(s[MJ]))))
    o = rows["obs2010"]
    summ.append("%-9s %-6s obs2010 %.3f | " % ("ssm", reg, np.nanmean(o[SO])) + " ".join(
        "%s %+.3f" % (lab, np.nanmean(rows[k][SO]) - np.nanmean(o[SO])) for k, _, lab in RUNS))

open("../data/phentest_flux_vs_obs_2010.txt", "w").write("\n".join(lines) + "\n\nSep-Oct bias vs obs 2010 (% = share of the CTRL bias removed)\n" + "\n".join(summ) + "\n")
print("Sep-Oct bias vs obs 2010 (% = share of CTRL bias removed)")
print("\n".join(summ))
