#!/usr/bin/env python
"""WFDE5 (CLM-format yearly files) -> HRLDAS LDASIN, 1 deg / 6-hourly.

The Noah-MP counterpart of the forcing LM4+ and CLM5 are driven with, so that
the three models share one forcing.  Source files are the CLM-format
/data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM_WFDE5/YYYY_wfde5.nc: 0.5 deg, 7
variables, 1460 six-hour MEANS per noleap year, time stamped at the window
midpoint (0.125 d = 03Z, then 09, 15, 21Z).

Derived from gswp3_to_ldasin_1deg6h.py; what differs and why:

  grid    same stride-2 subsample [::2, ::2].  Verified 2026-09-17
          (chk_wfde5_grid_1deg.py): WFDE5 LATIXY/LONGXY are identical to
          GSWP3's, and the subsample lands on the 1-deg setup file
          (HRLDAS_setup_GSWP3_1deg_d01.nc) exactly; XLONG differs by 360 on
          the western hemisphere, which is a convention, not an offset.

  time    files are stamped at the window MIDPOINT: YYYYMMDD03, 09, 15, 21.
          A 6-h mean belongs to the middle of its window.  Stamping it at the
          window start (00/06/12/18, as the instantaneous GSWP3 samples were)
          would advance the diurnal cycle by three hours -- SWDOWN peaking at
          09Z model time.  HRLDAS interpolates linearly between forcing times,
          which is what FMS data_override does for LM4+, so the two models
          then see the same forcing.  The run therefore starts at
          START_HOUR = 3 and its restarts fall at 03Z.

  leap    WFDE5 (CLM format) is noleap; Noah-MP runs a real calendar.  Feb 29
          is inserted as the average of Feb 28 and Mar 1 at each stamp, as the
          GSWP3 converter does.

  fill    WFDE5 is land-only (35.8 % of 0.5-deg cells valid, ocean = 1e20).
          On the 1-deg grid 18 of the 22,003 Noah-MP land cells (15 of them
          ice) sample a fill cell.  Every non-valid cell is filled with the
          nearest valid cell (longitude-periodic), the same treatment
          lm4p_offline_wfde5_to_atm.py gives LM4+.  Ocean cells get filled too;
          Noah-MP does not compute there.

  units   already HRLDAS units (K, kg/kg, Pa, m/s, W/m2, mm/s); WIND is total
          wind -> U2D, V2D = 0, as before.

Self-checks printed per year: file count, NaN count (must be 0), land-mean
T2D and RAINRATE (compare with the GSWP3 LDASIN of the same year: a few tenths
of a degree and a few percent are expected, more is a bug).

Usage (climate00, anaconda python):
  test   : python wfde5_to_ldasin_1deg6h.py YEAR OUTDIR NDAYS     # first NDAYS days
  range  : python wfde5_to_ldasin_1deg6h.py range Y0 Y1 OUTDIR
"""
import calendar
import os
import sys
from datetime import datetime, timedelta

import numpy as np
from netCDF4 import Dataset
from scipy.ndimage import distance_transform_edt

SRC_DIR = "/data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM_WFDE5"
SETUP = "/home/ydkoh/HRLDAS/forcing_GSWP3_1deg/init/HRLDAS_setup_GSWP3_1deg_d01.nc"
STR = 2                       # 0.5 deg -> 1 deg
HOURS = (3, 9, 15, 21)        # window midpoints
FILLTHRESH = 1e19             # WFDE5 ocean fill is 1e20

# (LDASIN name, WFDE5 var, units, description)
MAP = [
    ("T2D",      "TBOT",     "K",     "temperature"),
    ("Q2D",      "QBOT",     "kg/kg", "specific humidity"),
    ("U2D",      "WIND",     "m/s",   "zonal wind"),
    ("PSFC",     "PSRF",     "Pa",    "surface pressure"),
    ("LWDOWN",   "FLDS",     "W/m2",  "downward longwave radiation"),
    ("SWDOWN",   "FSDS",     "W/m2",  "downward shortwave radiation"),
    ("RAINRATE", "PRECTmms", "mm/s",  "rain rate"),
]


def srcfile(year):
    return os.path.join(SRC_DIR, "%d_wfde5.nc" % year)


def fill_indices(valid):
    """Index map (jj, ii) of the nearest valid cell, periodic in longitude."""
    wide = np.concatenate([valid, valid, valid], axis=1)
    _, (jj, ii) = distance_transform_edt(~wide, return_indices=True)
    nlon = valid.shape[1]
    jj = jj[:, nlon:2 * nlon]
    ii = ii[:, nlon:2 * nlon] - nlon
    return jj, ii % nlon


class Year(object):
    """One WFDE5 yearly file, subsampled to 1 deg and fill-corrected on read."""

    def __init__(self, year, jj=None, ii=None):
        self.year = year
        self.ds = Dataset(srcfile(year))
        self.nt = self.ds.dimensions["time"].size
        if self.nt != 1460:
            raise SystemExit("%s: %d steps, expected 1460 (noleap 6h)" % (srcfile(year), self.nt))
        if jj is None:
            tb = np.array(self.ds.variables["TBOT"][0, ::STR, ::STR], "f8")
            valid = np.isfinite(tb) & (tb < FILLTHRESH)
            jj, ii = fill_indices(valid)
            self.valid = valid
        self.jj, self.ii = jj, ii
        self.block0, self.block = -1, {}

    BLOCK = 80          # steps read per variable at a time (20 days): one
                        # strided read per step was ~1 file/s on the 10 GB
                        # yearly files; blocked reads are several times faster

    def _load(self, t):
        t0 = (t // self.BLOCK) * self.BLOCK
        t1 = min(t0 + self.BLOCK, self.nt)
        self.block = {}
        for ld, wv, _, _ in MAP:
            a = np.ma.filled(self.ds.variables[wv][t0:t1, ::STR, ::STR].astype("f8"), np.nan)
            a = np.where(np.isfinite(a) & (a < FILLTHRESH), a, np.nan)
            self.block[ld] = a[:, self.jj, self.ii]
        self.block0 = t0

    def slab(self, t):
        if not (self.block0 <= t < self.block0 + self.BLOCK) or not self.block:
            self._load(t)
        return {ld: self.block[ld][t - self.block0] for ld, _, _, _ in MAP}

    def close(self):
        self.ds.close()


def write_ldasin(outdir, dt, fields, nlat, nlon):
    out = os.path.join(outdir, dt.strftime("%Y%m%d%H") + ".LDASIN_DOMAIN1")
    o = Dataset(out, "w", format="NETCDF4")
    o.createDimension("west_east", nlon)
    o.createDimension("south_north", nlat)
    o.createDimension("Time", None)
    nnan = 0
    for ld, _, units, desc in MAP:
        v = o.createVariable(ld, "f4", ("Time", "south_north", "west_east"), zlib=True, complevel=1)
        v.description = desc
        v.units = units
        v[0, :, :] = fields[ld]
        nnan += int(np.isnan(fields[ld]).sum())
    v2 = o.createVariable("V2D", "f4", ("Time", "south_north", "west_east"), zlib=True, complevel=1)
    v2.description = "meridional wind"
    v2.units = "m/s"
    v2[0, :, :] = 0.0
    o.TITLE = ("WFDE5 v3.0 (CLM format) -> 1deg/6h LDASIN by wfde5_to_ldasin_1deg6h.py; "
               "stamps are 6h-window midpoints; non-valid cells nearest-filled")
    o.close()
    return nnan


def check_grid(yr):
    s = Dataset(SETUP)
    xlat = np.array(s.variables["XLAT"][0])
    xlon = np.array(s.variables["XLONG"][0])
    s.close()
    lat = np.array(yr.ds.variables["LATIXY"][::STR, ::STR])
    lon = np.array(yr.ds.variables["LONGXY"][::STR, ::STR])
    dlat = np.abs(lat - xlat).max()
    dlon = np.abs(((lon - xlon) + 180.0) % 360.0 - 180.0).max()
    if dlat > 1e-3 or dlon > 1e-3:
        raise SystemExit("grid mismatch vs setup: dlat %.4f dlon %.4f" % (dlat, dlon))
    return xlat.shape


def convert_year(year, outdir, ndays=None, land=None):
    yr = Year(year)
    nlat, nlon = check_grid(yr)
    if land is None:
        s = Dataset(SETUP)
        ivg = np.array(s.variables["IVGTYP"][0])
        s.close()
        land = (ivg != 17) & (ivg != 21) & (ivg > 0)
    nfill = int((land & ~yr.valid).sum())

    ndoy = 365 if ndays is None else min(365, ndays)
    written, nnan = 0, 0
    tsum, psum, nstep = 0.0, 0.0, 0
    real = datetime(year, 1, 1)                 # real-calendar date pointer
    for d in range(ndoy):                       # noleap day-of-year
        # insert Feb 29 on leap years before Mar 1 (noleap d == 59)
        if d == 59 and calendar.isleap(year) and ndays is None:
            for k, h in enumerate(HOURS):
                f28 = yr.slab(4 * 58 + k)
                m01 = yr.slab(4 * 59 + k)
                avg = {ld: 0.5 * (f28[ld] + m01[ld]) for ld in f28}
                nnan += write_ldasin(outdir, datetime(year, 2, 29, h), avg, nlat, nlon)
                written += 1
            real += timedelta(days=1)
        for k, h in enumerate(HOURS):
            fld = yr.slab(4 * d + k)
            nnan += write_ldasin(outdir, real + timedelta(hours=h), fld, nlat, nlon)
            written += 1
            tsum += np.nanmean(fld["T2D"][land])
            psum += np.nanmean(fld["RAINRATE"][land])
            nstep += 1
        real += timedelta(days=1)
    yr.close()
    print("year %d: %d files, NaN %d, land cells filled %d, land-mean T2D %.2f K, "
          "RAINRATE %.3f mm/d%s"
          % (year, written, nnan, nfill, tsum / nstep, psum / nstep * 86400.0,
             " (incl Feb29)" if calendar.isleap(year) and ndays is None else ""))
    if nnan:
        raise SystemExit("NaN in output for %d -- stop" % year)
    return written


if __name__ == "__main__":
    if sys.argv[1] == "range":
        y0, y1, outdir = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        os.makedirs(outdir, exist_ok=True)
        total = sum(convert_year(y, outdir) for y in range(y0, y1 + 1))
        print("TOTAL %d-%d: %d files -> %s" % (y0, y1, total, outdir))
    else:
        year, outdir = int(sys.argv[1]), sys.argv[2]
        ndays = int(sys.argv[3]) if len(sys.argv) > 3 else None
        os.makedirs(outdir, exist_ok=True)
        n = convert_year(year, outdir, ndays)
        print("wrote %d files -> %s" % (n, outdir))
