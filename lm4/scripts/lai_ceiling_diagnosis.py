#!/usr/bin/env python3
"""Where is LM4P's leaf area held down by its ceiling, and where by carbon?

This decides which parameter is worth tuning, and it has to be asked before any
tuning, because the two limits respond to different things and one of them does
not respond to LMA at all.

The ceiling on leaf carbon is

    bl_max = LMA * LAImax * crownarea * (1 - internal_gap_frac)

and leaf area index is

    LAI    = bl / (LMA * crownarea * (1 - internal_gap_frac))

Put bl = bl_max into the second and LMA cancels exactly: a cohort sitting at its
ceiling has LAI = LAImax whatever LMA is.  So in ceiling-limited places LMA is
not a knob -- LAImax is.  Only where bl stays below bl_max, because carbon never
arrived, does LMA set the leaf area for a given amount of carbon.

So: bl/bl_max per grid cell.  Near 1 means the ceiling binds.  Well below 1 means
carbon binds.  Both fields are per unit land area (kg C/m2) aggregated the same
way over cohorts, so their ratio is the fraction of the target leaf mass actually
achieved.

Uses the growing-season mean rather than the annual mean: a deciduous cell spends
half the year at bl = 0 by design, and averaging that in would label every
deciduous forest carbon-limited when it is simply winter.  Northern hemisphere
May-September, southern November-March.

Run after lm4p_to_latlon.py has written bl and bl_max.
"""

import os
import sys

import numpy as np
from netCDF4 import Dataset

D = os.environ.get("LM4P_LATLON_DIR", "/Volumes/data02/LM4P/postprocess/latlon")
OUTPUT = os.environ.get(
    "LM4P_CEILING_OUTPUT",
    "/Volumes/data02/LM4P/postprocess/lai_ceiling_1982_2020.npz",
)
CASE = "lm4p_ctl_1979-2024"
Y0, Y1 = 1982, 2020
NEAR_CEILING = 0.90          # bl/bl_max above this: the ceiling is what binds


def load(var):
    f = "%s/%s.%s.%d-%d.1deg.nc" % (D, CASE, var, Y0, Y1)
    with Dataset(f) as d:
        a = np.ma.filled(d.variables[var][:].astype("f8"), np.nan)
        lat = d.variables["lat"][:]
        lon = d.variables["lon"][:]
    return np.where(a > 1e19, np.nan, a), np.asarray(lat), np.asarray(lon)


def weighted_percentile(values, weights, percentile):
    """Return a percentile using grid-cell area weights."""
    valid = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[valid]
    weights = weights[valid]
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cumulative = np.cumsum(weights) - 0.5 * weights
    cumulative /= weights.sum()
    return np.interp(percentile / 100.0, cumulative, values)


def growing_season(a, lat):
    """Mean over the local growing season: NH May-Sep, SH Nov-Mar."""
    nm = a.shape[0]
    mon = np.arange(nm) % 12                      # 0=Jan
    nh = np.isin(mon, [4, 5, 6, 7, 8])
    sh = np.isin(mon, [10, 11, 0, 1, 2])
    north = lat[:, None] >= 0
    def mean_without_empty_slice_warning(x):
        count = np.isfinite(x).sum(axis=0)
        return np.divide(np.nansum(x, axis=0), count,
                         out=np.full(x.shape[1:], np.nan), where=count > 0)

    out = np.where(north,
                   mean_without_empty_slice_warning(a[nh]),
                   mean_without_empty_slice_warning(a[sh]))
    return out


bl, lat, lon = load("bl")
blmax, lat_blmax, lon_blmax = load("bl_max")
lai, lat_lai, lon_lai = load("lai")

if not (np.array_equal(lat, lat_blmax) and np.array_equal(lat, lat_lai)
        and np.array_equal(lon, lon_blmax) and np.array_equal(lon, lon_lai)):
    raise SystemExit("bl, bl_max, and lai grids do not match")

bl_g = growing_season(bl, lat)
blmax_g = growing_season(blmax, lat)
lai_g = growing_season(lai, lat)

ok = np.isfinite(bl_g) & np.isfinite(blmax_g) & (blmax_g > 1e-4)
ratio = np.full_like(bl_g, np.nan)
ratio[ok] = bl_g[ok] / blmax_g[ok]

# area weight: cos(lat), because a 1-degree cell at 60N is half the area of one
# at the equator and an unweighted count would over-report the boreal zone
w = np.broadcast_to(np.cos(np.deg2rad(lat))[:, None], bl_g.shape).copy()
w = np.where(ok, w, 0.0)


def frac(mask):
    return 100.0 * w[mask & ok].sum() / w[ok].sum()


print("LM4P leaf-ceiling diagnosis  %d-%d, growing-season mean" % (Y0, Y1))
print("=" * 66)
print("land cells with a leaf target: %d  (%.1f%% of grid)"
      % (ok.sum(), 100.0 * ok.mean()))
print()
print("bl/bl_max, area-weighted:")
for p in (5, 25, 50, 75, 95):
    print("   p%-3d %.3f" % (p, weighted_percentile(ratio, w, p)))
print("   mean %.3f" % (np.nansum(ratio * w) / w.sum()))
print()
print("how much of the vegetated land is held by which limit:")
print("   ceiling-limited  bl/bl_max >= %.2f : %5.1f %%" % (NEAR_CEILING, frac(ratio >= NEAR_CEILING)))
print("   intermediate     0.50-%.2f         : %5.1f %%" % (NEAR_CEILING, frac((ratio >= 0.50) & (ratio < NEAR_CEILING))))
print("   carbon-limited   bl/bl_max <  0.50 : %5.1f %%" % frac(ratio < 0.50))
print()
print("   -> in the ceiling-limited fraction, LMA has NO effect on LAI;")
print("      LAImax is the only parameter that moves it.")
print()

print("by latitude band (area-weighted):")
print("  %-14s %7s %7s %7s %9s" % ("band", "bl/blmax", "LAI", "cells", "ceiling%"))
bands = [(-90, -60, "60-90S"), (-60, -30, "30-60S"), (-30, 0, "0-30S"),
         (0, 30, "0-30N"), (30, 60, "30-60N"), (60, 90, "60-90N")]
for lo, hi, name in bands:
    m = (lat >= lo) & (lat < hi)
    sel = np.zeros_like(ok); sel[m, :] = True
    sel &= ok
    if sel.sum() == 0:
        print("  %-14s %7s" % (name, "-")); continue
    ww = w[sel]
    print("  %-14s %7.3f %7.2f %7d %8.1f" %
          (name,
           np.nansum(ratio[sel] * ww) / ww.sum(),
           np.nansum(lai_g[sel] * ww) / ww.sum(),
           sel.sum(),
           100.0 * w[sel & (ratio >= NEAR_CEILING)].sum() / ww.sum()))

print()
print("named regions (growing-season mean):")
for name, la, lo in [("Amazon", -3, -60), ("Congo", 0, 20), ("Borneo", 2, 113),
                     ("US Midwest", 41, -93), ("Amur / NE China", 48, 128),
                     ("Siberia taiga", 62, 100), ("Canada boreal", 55, -105),
                     ("Scandinavia", 65, 20), ("Sahel", 14, 5),
                     ("Tibetan Plateau", 33, 90), ("E Australia", -30, 148)]:
    j = int(round(la + 90 - 0.5)); i = int(round(lo + 180 - 0.5))
    r = ratio[j, i]; L = lai_g[j, i]
    tag = "" if not np.isfinite(r) else ("  <- ceiling" if r >= NEAR_CEILING
                                         else ("  <- carbon" if r < 0.5 else ""))
    print("  %-18s bl/blmax %s   LAI %s%s"
          % (name,
             "  nan" if not np.isfinite(r) else "%5.3f" % r,
             "  nan" if not np.isfinite(L) else "%5.2f" % L, tag))

# ---------------------------------------------------------------------------
# Native C96 check.  The 1-degree fields above come from a nearest-neighbour
# regrid meant for looking at maps: about 16 % of the C96 land points never
# land in any 1-degree cell, and some are copied into many cells at high
# latitude.  cos(lat) on the target grid therefore does not reproduce the
# model's own land_area weighting.  The headline fractions are recomputed here
# straight from the tile files, weighted by the land_area each point carries,
# so the number that goes into a report is the model's and not the regrid's.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "postprocess"))
from lm4p_to_latlon import NTILE, land_coords, read_var   # noqa: E402

CASEDIR = os.environ.get("LM4P_CASE_DIR",
                         "/Volumes/data02/LM4P/cases/%s" % CASE)
GRIDDIR = os.environ.get("LM4P_GRID_DIR", "/Volumes/data02/LM4P/postprocess/grid")

nlat_pt, _ = land_coords(CASEDIR, Y0, GRIDDIR)
area_pt = np.concatenate([
    np.ma.filled(Dataset("%s/archive/y%d/%d0101.land_static.tile%d.nc"
                         % (CASEDIR, Y0, Y0, t)).variables["land_area"][:]
                 .astype("f8"), np.nan)
    for t in range(1, NTILE + 1)])

bl_n = np.concatenate([read_var(CASEDIR, y, "bl")[0] for y in range(Y0, Y1 + 1)])
blmax_n = np.concatenate([read_var(CASEDIR, y, "bl_max")[0] for y in range(Y0, Y1 + 1)])
# growing_season() expects (time, lat, lon); a trailing axis of one makes the
# point list look like a one-column map so the same hemisphere logic applies
bl_ng = growing_season(bl_n[:, :, None], nlat_pt)[:, 0]
blmax_ng = growing_season(blmax_n[:, :, None], nlat_pt)[:, 0]

ok_n = (np.isfinite(bl_ng) & np.isfinite(blmax_ng) & (blmax_ng > 1e-4)
        & np.isfinite(area_pt) & (area_pt > 0))
ratio_n = np.full_like(bl_ng, np.nan)
ratio_n[ok_n] = bl_ng[ok_n] / blmax_ng[ok_n]
w_n = np.where(ok_n, area_pt, 0.0)


def frac_n(mask):
    return 100.0 * w_n[mask & ok_n].sum() / w_n[ok_n].sum()


print()
print("native C96 check (land_area-weighted, %d of %d land points with a leaf target)"
      % (ok_n.sum(), ok_n.size))
print("  %-34s %8s %8s" % ("", "1deg", "native"))
print("  %-34s %8.3f %8.3f" % ("bl/bl_max p50",
                                weighted_percentile(ratio, w, 50),
                                weighted_percentile(ratio_n, w_n, 50)))
print("  %-34s %8.3f %8.3f" % ("bl/bl_max mean",
                                np.nansum(ratio * w) / w.sum(),
                                np.nansum(ratio_n * w_n) / w_n.sum()))
print("  %-34s %7.1f%% %7.1f%%" % ("ceiling-limited  >= %.2f" % NEAR_CEILING,
                                    frac(ratio >= NEAR_CEILING),
                                    frac_n(ratio_n >= NEAR_CEILING)))
print("  %-34s %7.1f%% %7.1f%%" % ("intermediate     0.50-%.2f" % NEAR_CEILING,
                                    frac((ratio >= 0.50) & (ratio < NEAR_CEILING)),
                                    frac_n((ratio_n >= 0.50) & (ratio_n < NEAR_CEILING))))
print("  %-34s %7.1f%% %7.1f%%" % ("carbon-limited   <  0.50",
                                    frac(ratio < 0.50), frac_n(ratio_n < 0.50)))
print("  -> quote the native column; the 1deg column is the map's, not the model's")

np.savez_compressed(OUTPUT,
                    lat=lat, lon=lon, ratio=ratio, lai=lai_g,
                    bl=bl_g, blmax=blmax_g,
                    native_lat=nlat_pt, native_area=area_pt, native_ratio=ratio_n)
print("\nwrote %s" % OUTPUT)
