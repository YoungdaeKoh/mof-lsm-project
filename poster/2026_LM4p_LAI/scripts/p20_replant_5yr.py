#!/usr/bin/env python3
"""Replanted run, years 1-6 after re-seeding (2010 = replant1y_np48_d, 2011-2015 = replant_2011_2015) vs CTRL
(ctl production, same WFDE5 years) vs GIMMS LAI4g. Same weather each year -> differences = species distribution.
input : ../data/replant5y/{ctl,repl}_species_share_julyYYYY_c96.npz (phentest_species_frac_cells.py, July leaf area)
        ../data/base_species_share_july2010_c96.npz, ../data/replant1y_species_share_july2010_c96.npz
        LAI 1 deg: ../data/{base,replant1y}.lai.2010-2010.1deg.nc,
                   /Volumes/data02/LM4P/postprocess/latlon/lm4p_ctl_1979-2024.lai.2011-2015.1deg.nc
                   /Volumes/data02/LM4P/postprocess/latlon/replant_2011_2015.lai.2011-2015.1deg.nc
        ../data/gimms_lai_mon_1982_2020.nc
output: ../data/replant5y/replant_5yr_summary.txt (console = same compact table)
"""
import warnings
import numpy as np
import netCDF4 as nc
import regionmask

LL = "/Volumes/data02/LM4P/postprocess/latlon/"
YEARS = range(2010, 2016)
NORTH = ["NWN", "NEN", "NEU", "WSB", "ESB", "RFE"]

def shares(f):
    z = np.load(f, allow_pickle=True); names = list(z["species"]); sh = np.nan_to_num(z["share"].astype("f8"))
    lat, a = z["lat"], z["area"]
    res = {}
    for lab, m in (("N", (lat >= 50) & (lat < 75)), ("T", np.abs(lat) < 30)):
        k = m & (sh.sum(0) > 0.05); w = a[k]
        res[lab] = {n: 100 * np.sum(w * sh[i][k]) / w.sum() for i, n in enumerate(names)}
    return res

def lai_year(kind, y):
    if y == 2010:
        f = "../data/%s.lai.2010-2010.1deg.nc" % ("base" if kind == "ctl" else "replant1y"); i0 = 0
    else:
        f = LL + ("lm4p_ctl_1979-2024" if kind == "ctl" else "replant_2011_2015") + ".lai.2011-2015.1deg.nc"; i0 = (y - 2011) * 12
    return np.ma.filled(nc.Dataset(f).variables["lai"][i0:i0 + 12].astype("f8"), np.nan)

g = nc.Dataset("../data/gimms_lai_mon_1982_2020.nc")
gname = [v for v in g.variables if g.variables[v].ndim == 3][0]
lat = np.asarray(g.variables["lat"][:]); lon = np.asarray(g.variables["lon"][:])
W = np.cos(np.radians(lat))[:, None] * np.ones((1, lon.size))
ar6 = regionmask.defined_regions.ar6.land
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    m3 = ar6.mask_3D(lon, lat)
north = np.zeros(W.shape, bool)
for ab in NORTH:
    north |= m3.sel(region=ar6.map_keys(ab)).values.astype(bool)

def wmean(v, w):
    return np.array([np.nansum(v[k] * w) / w.sum() for k in range(12)])

lines = ["yr  age | 50-75N July leaf-area share %  picea / larix / acer / c3grass   CTRL -> REPL | tropics c4 / c3 grass  CTRL -> REPL",
         "        | LAI bias vs GIMMS (annual %)  50-70N CTRL/REPL, tropics CTRL/REPL | NORTH6 May-Jun and Sep-Oct mean LAI: GIMMS / CTRL / REPL"]
for age, y in enumerate(YEARS, start=1):
    fc = "../data/base_species_share_july2010_c96.npz" if y == 2010 else f"../data/replant5y/ctl_species_share_july{y}_c96.npz"
    fr = "../data/replant1y_species_share_july2010_c96.npz" if y == 2010 else f"../data/replant5y/repl_species_share_july{y}_c96.npz"
    sc, sr = shares(fc), shares(fr)
    obs = np.ma.filled(g.variables[gname][(y - 1982) * 12:(y - 1982) * 12 + 12].astype("f8"), np.nan)
    c, r = lai_year("ctl", y), lai_year("repl", y)
    ok = np.isfinite(obs).all(0) & np.isfinite(c).all(0) & np.isfinite(r).all(0)
    out = []
    for a0, a1 in ((50, 70), (-30, 30)):
        w = W * ok * ((lat[:, None] >= a0) & (lat[:, None] < a1))
        o, cc, rr = wmean(obs, w).mean(), wmean(c, w).mean(), wmean(r, w).mean()
        out.append(f"{100*(cc-o)/o:+4.0f}/{100*(rr-o)/o:+4.0f}%")
    w = W * ok * north
    o, cc, rr = wmean(obs, w), wmean(c, w), wmean(r, w)
    N, T = sc["N"], sc["T"]
    lines.append(f"{y} {age:3d} | " + " / ".join(f"{N[s]:4.1f}" for s in ("picea", "larix", "acer", "c3grass")) + "  ->  "
                 + " / ".join(f"{sr['N'][s]:4.1f}" for s in ("picea", "larix", "acer", "c3grass"))
                 + f" | {T['c4grass']:4.1f}/{T['c3grass']:4.1f} -> {sr['T']['c4grass']:4.1f}/{sr['T']['c3grass']:4.1f}")
    lines.append(f"         | 50-70N {out[0]}, tropics {out[1]} | MJ {o[4:6].mean():.2f}/{cc[4:6].mean():.2f}/{rr[4:6].mean():.2f}"
                 f"  SO {o[8:10].mean():.2f}/{cc[8:10].mean():.2f}/{rr[8:10].mean():.2f}")
open("../data/replant5y/replant_5yr_summary.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
