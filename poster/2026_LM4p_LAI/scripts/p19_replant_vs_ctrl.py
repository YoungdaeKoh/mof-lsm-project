#!/usr/bin/env python3
"""Replanted species distribution (replant1y_np48_d) vs CTRL (base), monthly LAI 2010, against GIMMS.
input : ../data/{base,replant1y}.lai.2010-2010.1deg.nc  (same 2010-01-01 restart physics; replant1y = species
        re-seeded from the CLM5 map, CTRL phenology, offline_fast tables -- land physics bit-identical to ctl tables)
        ../data/gimms_lai_mon_1982_2020.nc (year 2010)
output: ../data/replant_vs_ctrl_2010.txt (console prints the compact summary only)
Common valid cells, cos-lat weights. Regions = AR6 land used for the day-length runs (LM4 notes 13.71).
Caveat: one year after re-seeding -> vegetation still young; this shows the direction, not an equilibrium.
"""
import warnings
import numpy as np
import netCDF4 as nc
import regionmask

YEAR = 2010
REGIONS = ["NWN", "NEN", "NEU", "WCE", "RAR", "WSB", "ESB", "RFE", "ENA", "EAS", "NSA", "SAM", "WAF", "CAF", "SEA", "SES"]
BANDS = [("tropics 30S-30N", -30, 30), ("20-60S", -60, -20), ("50-70N", 50, 70), ("30-50N", 30, 50)]

g = nc.Dataset("../data/gimms_lai_mon_1982_2020.nc")
gname = [v for v in g.variables if g.variables[v].ndim == 3][0]
i0 = (YEAR - 1982) * 12
obs = np.ma.filled(g.variables[gname][i0:i0 + 12].astype("f8"), np.nan)
lat = np.asarray(g.variables["lat"][:]); lon = np.asarray(g.variables["lon"][:])
run = {k: np.ma.filled(nc.Dataset("../data/%s.lai.%d-%d.1deg.nc" % (k, YEAR, YEAR)).variables["lai"][:].astype("f8"),
                       np.nan) for k in ("base", "replant1y")}
for k, v in run.items():
    assert v.shape == obs.shape, (k, v.shape, obs.shape)
ok = np.isfinite(obs).all(0) & np.isfinite(run["base"]).all(0) & np.isfinite(run["replant1y"]).all(0)
W = np.cos(np.radians(lat))[:, None] * np.ones((1, lon.size))
ar6 = regionmask.defined_regions.ar6.land
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    m3 = ar6.mask_3D(lon, lat)

def series(v, w):
    return np.array([np.nansum(v[k] * w) / w.sum() for k in range(12)])

def row(name, w):
    o, b, r = series(obs, w), series(run["base"], w), series(run["replant1y"], w)
    ann = lambda s: s.mean()
    mj, so, jja, son = slice(4, 6), slice(8, 10), slice(5, 8), slice(8, 11)
    gap_b, gap_r = b[so].mean() - o[so].mean(), r[so].mean() - o[so].mean()
    return (f"{name:16s} {int((w > 0).sum()):5d} | ann {ann(o):5.2f} {ann(b):5.2f} {ann(r):5.2f} "
            f"({100*(ann(b)-ann(o))/ann(o):+5.0f}% -> {100*(ann(r)-ann(o))/ann(o):+5.0f}%) | "
            f"MJ {o[mj].mean():5.2f} {b[mj].mean():5.2f} {r[mj].mean():5.2f} | "
            f"SO {o[so].mean():5.2f} {b[so].mean():5.2f} {r[so].mean():5.2f} gapclosed {100*(gap_b-gap_r)/gap_b if abs(gap_b) > 1e-6 else np.nan:+5.0f}% | "
            f"MAE12 {np.abs(b-o).mean():4.2f} -> {np.abs(r-o).mean():4.2f}")

hdr = (f"{'region':16s} {'cells':>5s} | ann GIMMS CTRL REPL (bias% CTRL -> REPL) | MJ GIMMS CTRL REPL | "
       f"SO GIMMS CTRL REPL gap-closed | MAE12 CTRL -> REPL")
lines = [hdr]
for name, a0, a1 in BANDS:
    lines.append(row(name, W * ok * ((lat[:, None] >= a0) & (lat[:, None] < a1))))
lines.append(row("global land", W * ok))
for ab in REGIONS:
    lines.append(row(ab, W * (ok & m3.sel(region=ar6.map_keys(ab)).values.astype(bool))))
open("../data/replant_vs_ctrl_2010.txt", "w").write(
    "# Monthly LAI 2010: GIMMS vs CTRL (base) vs REPL (replant1y_np48_d), common valid cells, cos-lat\n"
    "# gapclosed = share of the CTRL-GIMMS Sep-Oct gap removed by REPL; MAE12 = mean abs monthly error\n"
    + "\n".join(lines) + "\n")
print("\n".join(lines))
