"""Has the CLM5 post-AD spin-up converged?

The criterion CLM5-BGC states, and the one this project adopted, is a per-cell
one: total ecosystem carbon drifting by no more than 1 gC/m2/yr in at least 97 %
of cells.  A global mean can sit still while individual cells are still moving in
opposite directions, so the test has to be done cell by cell and then counted.

The drift is a least-squares slope over the last N years of annual means, not a
difference between the first and last year -- a difference is at the mercy of two
particular years, while a slope uses all of them.

Reported alongside, because they converge at different rates and knowing which
one is holding the run back tells you whether to keep going:
  TOTSOMC   soil organic matter, the slowest pool
  TOTVEGC   vegetation carbon
  TLAI      leaf area
  TWS       total water storage
Cells are area-weighted for the means; the 97 % count is unweighted, as the
criterion is stated per cell.

Run on climate00 (reads the raw archive directly).

Usage: python clm5_postad_convergence.py [window_years]
Output: /data2/ydkoh/cesm2_output/clm5_postad_convergence.csv
"""
import glob
import os
import re
import sys
import numpy as np
import netCDF4 as nc

ARCH = "/home/ydkoh/CESM/spinup_raw/clm5_BGC_PAD"
OUT = "/data2/ydkoh/cesm2_output/clm5_postad_convergence.csv"
WINDOW = int(sys.argv[1]) if len(sys.argv) > 1 else 20
VARS = ["TOTECOSYSC", "TOTSOMC", "TOTVEGC", "TLAI", "TWS"]
CRIT = 1.0                      # gC/m2/yr, the per-cell threshold
FRAC = 0.97                     # fraction of cells that must meet it

files = sorted(glob.glob("%s/*.clm2.h0.*.nc" % ARCH))
if not files:
    raise SystemExit("no history files in %s" % ARCH)
years = np.array([int(re.search(r"h0\.(\d{4})-", os.path.basename(f)).group(1))
                  for f in files])
uyr = np.unique(years)
print("post-AD history: %d files, model years %04d-%04d"
      % (len(files), uyr[0], uyr[-1]))

# a year is only usable if all twelve months are present
full = np.array([y for y in uyr if (years == y).sum() == 12])
if full.size < 5:
    raise SystemExit("only %d complete years; too few to fit a trend" % full.size)
if full.size < WINDOW:
    print("  only %d complete years, shortening the window from %d"
          % (full.size, WINDOW))
    WINDOW = full.size
print("complete years: %d (%04d-%04d), trend window: last %d\n"
      % (full.size, full[0], full[-1], WINDOW))

d0 = nc.Dataset(files[0])
lat = np.array(d0.variables["lat"][:], "f8")
area = np.array(d0.variables["area"][:], "f8") if "area" in d0.variables else None
landfrac = (np.array(d0.variables["landfrac"][:], "f8")
            if "landfrac" in d0.variables else None)
d0.close()
W = (np.cos(np.deg2rad(lat))[:, None] if area is None else area)
if landfrac is not None:
    W = W * np.where(np.isfinite(landfrac), landfrac, 0.0)

fit_years = full[-WINDOW:]
t = fit_years - fit_years.mean()
den = (t ** 2).sum()

rows = []
print("%-12s %10s %12s %14s %10s" %
      ("variable", "mean", "global drift", "cells <=1 g/m2/yr", "verdict"))
for var in VARS:
    ann = []
    for y in fit_years:
        sel = [f for f, yy in zip(files, years) if yy == y]
        acc = None
        for f in sel:
            dd = nc.Dataset(f)
            a = np.ma.filled(dd.variables[var][0].astype("f8"), np.nan)
            dd.close()
            acc = a if acc is None else acc + a
        ann.append(acc / len(sel))
    ann = np.stack(ann)                                  # (year, lat, lon)

    valid = np.all(np.isfinite(ann), axis=0)
    w = np.where(valid, W, 0.0)
    gmean = np.nansum(np.where(valid, ann[-1], 0) * w) / w.sum()

    an = ann - ann.mean(axis=0)
    slope = (an * t[:, None, None]).sum(axis=0) / den    # per year, per cell
    gdrift = np.nansum(np.where(valid, slope, 0) * w) / w.sum()

    if var in ("TOTECOSYSC", "TOTSOMC", "TOTVEGC"):
        ok = np.abs(slope[valid]) <= CRIT                 # already gC/m2/yr
        frac = ok.mean()
        verdict = "converged" if frac >= FRAC else "not yet"
        fs = "%9.1f %%" % (100 * frac)
    else:
        frac, verdict, fs = np.nan, "-", "-"

    print("%-12s %10.2f %12.4f %14s %10s" % (var, gmean, gdrift, fs, verdict))
    rows.append([var, gmean, gdrift, 100 * frac if np.isfinite(frac) else -1])

with open(OUT, "w") as fh:
    fh.write("variable,mean,global_drift_per_yr,pct_cells_within_1gC\n")
    for r in rows:
        fh.write("%s,%.6f,%.6f,%.3f\n" % tuple(r))
print("\nwrote %s" % OUT)
print("criterion: TOTECOSYSC drift <= %.0f gC/m2/yr in >= %.0f %% of cells"
      % (CRIT, 100 * FRAC))
