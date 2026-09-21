#!/usr/bin/env python
"""Noah-MP production run: 6-hourly LDASOUT -> monthly means (all variables) and
daily means (key variables), one CF-compliant file each per year.

Why this exists: HRLDAS writes instantaneous snapshots at every OUTPUT_TIMESTEP
and cannot average, so the 6-h files (03/09/15/21Z, the WFDE5 stamps) are the
raw record and the means are formed here.  The 03Z-vs-15Z land-mean LH differs
by ~20 W/m2 (notes 12), so a single daily snapshot would not do.

Averaging
  monthly  = mean of all 6-h files whose stamp falls in the month (equal
             weights; 4 stamps per day, so this equals the mean of daily means)
  daily    = mean of the 4 stamps of the calendar day
  accumulated variables (ACC below, units mm since the run/spin-up started)
           -> mean rate over the period, mm/day, from the difference between
             the last file of the period and the last file of the previous
             period (first period of a year: the first file of that year)

Grid: 1 deg, lat ascending -89.75..89.25 (XLAT[:,0]), lon written as 0..360
(XLONG % 360, 0.25..359.75) so that it is monotonic.  Static IVGTYP/ISLTYP are
copied once.  Layer dimensions are moved to (time, layer, lat, lon).

Usage (climate, anaconda python):
  python postproc_ldasout.py YEAR [--months N] [--rundir DIR] [--outdir DIR]
  --months N   process only the first N months (test)
Output: OUTDIR/noahmp_prod_mon_YEAR.nc, OUTDIR/noahmp_prod_day_YEAR.nc
"""
import argparse
import calendar
import glob
import os
import sys
from datetime import datetime, timedelta

import numpy as np
from netCDF4 import Dataset, date2num

P = argparse.ArgumentParser()
P.add_argument("year", type=int)
P.add_argument("--months", type=int, default=12)
P.add_argument("--rundir", default="/home/ydkoh/HRLDAS/forcing_WFDE5_1deg/prod_1979_2023")
P.add_argument("--outdir", default="/home/ydkoh/HRLDAS/forcing_WFDE5_1deg/prod_1979_2023/postproc")
A = P.parse_args()
SETUP = "/home/ydkoh/HRLDAS/forcing_GSWP3_1deg/init/HRLDAS_setup_GSWP3_1deg_d01.nc"

ACC = ["UGDRNOFF", "SFCRNOFF", "ACSNOW", "ACSNOM"]          # accumulated mm -> mm/day
STATIC = ["IVGTYP", "ISLTYP"]
SKIP = ["Times"]
DAILY = ["LH", "HFX", "FSA", "FIRA", "GRDFLX", "SWFORC", "LWFORC", "RAINRATE",
         "T2MV", "T2MB", "TRAD", "TG", "TV", "FSNO", "SNEQV", "SNOWH", "ISNOW",
         "LAI", "GPP", "NEE", "NPP", "ECAN", "ETRAN", "EDIR", "ZWT", "FVEG",
         "SOIL_M", "SOIL_T"] + ACC
TIME_UNITS = "days since 1979-01-01 00:00:00"

os.makedirs(A.outdir, exist_ok=True)
files = sorted(glob.glob(os.path.join(A.rundir, "%d??????.LDASOUT_DOMAIN1" % A.year)))
if not files:
    sys.exit("no LDASOUT for %d in %s" % (A.year, A.rundir))
stamp = lambda f: datetime.strptime(os.path.basename(f)[:10], "%Y%m%d%H")
files = [f for f in files if stamp(f).month <= A.months]
print("%d: %d files, %s .. %s" % (A.year, len(files), os.path.basename(files[0])[:10], os.path.basename(files[-1])[:10]))

# --- grid and variable inventory from the first file --------------------------
s = Dataset(SETUP)
lat = np.array(s.variables["XLAT"][0, :, 0], "f8")
lon = np.array(s.variables["XLONG"][0, 0, :], "f8") % 360.0
s.close()
assert np.all(np.diff(lat) > 0) and np.all(np.diff(lon) > 0), "grid not monotonic"

d0 = Dataset(files[0])
VARS = []
for name, v in d0.variables.items():
    if name in SKIP or name in STATIC:
        continue
    dims = v.dimensions
    layer = None if len(dims) == 3 else dims[2]        # (Time, sn, layer, we)
    VARS.append((name, layer, v.units if "units" in v.ncattrs() else "", getattr(v, "description", "")))
LAYERDIMS = {dn: d0.dimensions[dn].size for dn in d0.dimensions if dn not in ("Time", "DateStrLen")}
static = {n: np.array(d0.variables[n][0]) for n in STATIC}
d0.close()
if A.months == 12:
    assert len(files) in (1459, 1460, 1463, 1464), "unexpected file count %d" % len(files)


def read(f):
    d = Dataset(f)
    out = {}
    for name, layer, _, _ in VARS:
        a = np.ma.filled(d.variables[name][0].astype("f8"), np.nan)
        a[a < -1e30] = np.nan                            # HRLDAS water fill (-1e33, no attribute)
        if layer is not None:
            a = np.moveaxis(a, 1, 0)                     # (sn, layer, we) -> (layer, sn, we)
        out[name] = a
    d.close()
    return out


def new_file(path, ntime, tunits_note):
    o = Dataset(path, "w", format="NETCDF4")
    o.createDimension("time", None)
    o.createDimension("lat", lat.size)
    o.createDimension("lon", lon.size)
    for dn, n in LAYERDIMS.items():
        if dn not in ("south_north", "west_east", "south_north_stag", "west_east_stag"):
            o.createDimension(dn, n)
    t = o.createVariable("time", "f8", ("time",)); t.units = TIME_UNITS; t.calendar = "standard"
    t.long_name = tunits_note
    la = o.createVariable("lat", "f8", ("lat",)); la.units = "degrees_north"; la[:] = lat
    lo = o.createVariable("lon", "f8", ("lon",)); lo.units = "degrees_east"; lo[:] = lon
    for n in STATIC:
        v = o.createVariable(n, "i4", ("lat", "lon"), zlib=True, complevel=1); v[:] = static[n]
    o.source = "Noah-MP v5.2.1 HRLDAS offline, WFDE5 1deg/6h, DVEG=5, run prod_1979_2023"
    o.note = ("means of instantaneous 6-h snapshots at 03/09/15/21Z; " + ", ".join(ACC) +
              " are mean rates (mm/day) from accumulated totals")
    return o


def add_var(o, name, layer, units, desc):
    dims = ("time", layer, "lat", "lon") if layer else ("time", "lat", "lon")
    v = o.createVariable(name, "f4", dims, zlib=True, complevel=1, fill_value=np.float32(-9999.0))
    v.units = "mm/day" if name in ACC else units
    if desc:
        v.description = desc
    return v


# --- accumulate ---------------------------------------------------------------
def periods(files, key):
    groups = {}
    for f in files:
        groups.setdefault(key(stamp(f)), []).append(f)
    return groups

mon = periods(files, lambda t: t.month)
day = periods(files, lambda t: (t.month, t.day))

mon_out = new_file(os.path.join(A.outdir, "noahmp_prod_mon_%d.nc" % A.year), None, "mid-month")
day_out = new_file(os.path.join(A.outdir, "noahmp_prod_day_%d.nc" % A.year), None, "mid-day (12Z)")
mv = {n: add_var(mon_out, n, l, u, d) for n, l, u, d in VARS}
dv = {n: add_var(day_out, n, l, u, d) for n, l, u, d in VARS if n in DAILY}

prev_acc = None                                            # last file of the previous period
prev_t = None
mi = di = 0
first_of_year = read(files[0])
for m in sorted(mon):
    msum = {}; mcount = 0
    for dkey in sorted(k for k in day if k[0] == m):
        dsum = {}; dcount = 0
        for f in day[dkey]:
            x = read(f)
            for n in x:
                dsum[n] = dsum.get(n, 0) + x[n]
                msum[n] = msum.get(n, 0) + x[n]
            dcount += 1; mcount += 1
        t_last = stamp(day[dkey][-1])
        if prev_acc is None:
            prev_acc = first_of_year; prev_t = stamp(files[0])
        for n in DAILY:
            if n in ACC:
                secs = (t_last - prev_t).total_seconds()
                dv[n][di] = (x[n] - prev_acc[n]) / secs * 86400.0 if secs > 0 else np.nan
            else:
                dv[n][di] = dsum[n] / dcount
        day_out.variables["time"][di] = date2num(datetime(A.year, dkey[0], dkey[1], 12), TIME_UNITS)
        di += 1
        prev_acc, prev_t = x, t_last
    # monthly: accumulated rate over the month = last file of month - last file of previous month
    for n, l, _, _ in VARS:
        if n not in ACC:                                   # ACC filled below from month boundaries
            mv[n][mi] = msum[n] / mcount
    mon_out.variables["time"][mi] = date2num(datetime(A.year, m, 15, 12), TIME_UNITS)
    mi += 1
    print("  month %02d: %d files" % (m, mcount), flush=True)

# accumulated monthly rates: recompute from month-boundary files (cheap: 13 reads)
bounds = [files[0]] + [mon[m][-1] for m in sorted(mon)]
acc_vals = []
for f in bounds:
    d = Dataset(f)
    acc_vals.append({n: np.where(d.variables[n][0].astype("f8") < -1e30, np.nan,
                                 d.variables[n][0].astype("f8")) for n in ACC})
    d.close()
for i, m in enumerate(sorted(mon)):
    secs = (stamp(bounds[i + 1]) - stamp(bounds[i])).total_seconds()
    for n in ACC:
        mv[n][i] = (acc_vals[i + 1][n] - acc_vals[i][n]) / secs * 86400.0

mon_out.close(); day_out.close()
# --- self-check ---------------------------------------------------------------
o = Dataset(os.path.join(A.outdir, "noahmp_prod_mon_%d.nc" % A.year))
lh = np.array(o.variables["LH"][:]); ro = np.array(o.variables["UGDRNOFF"][:])
land = (static["IVGTYP"] > 0) & (static["IVGTYP"] != 17) & (static["IVGTYP"] != 21)
print("wrote mon (%d months) / day (%d days); LH land-mean by month: %s ; UGDRNOFF mm/day: %s ; NaN(LH,land) %d"
      % (mi, di, np.round([np.nanmean(x[land]) for x in lh], 1).tolist(),
         np.round([np.nanmean(x[land]) for x in ro], 2).tolist(), int(np.isnan(lh[:, land]).sum())))
o.close()
