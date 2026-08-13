"""Append next-year boundary records to the 1979-2024 forcing set.

Same job as append_boundary.py, which covered 1981-2010: a segment starts at
Jan 1 03:00 and runs 365 days, ending at Jan 1 03:00 of the following year,
while the converted file's own last record is Dec 31 21:00 (day 364.875).  Two
records (day 365.125, 365.375) taken from the next year close that gap.

Two differences from the 1981-2010 version, both because the production run now
spans 1979-2024:

  * range is 1979-2024, so the sixteen newly converted years get their boundary.

  * the boundary is rewritten even when the file already carries 1462 records.
    Under the old range 2010 was the last year, so its two appended records were
    wrapped from 1981.  In the 46-year run 2010 is an interior year and must be
    followed by 2011, otherwise there is a six-hour seam in the middle of the
    production period.  Overwriting is safe: indices 1460-1461 hold nothing but
    that boundary.

Only 2024, the true last year, still wraps -- to 1979.
"""
import os
import numpy as np
import netCDF4 as nc

DST = "/data2/ydkoh/lm4/forcing_WFDE5_lm4p"
FIRST, LAST = 1979, 2024
NBASE = 1460                  # records the conversion itself writes
NAPP = 2                      # boundary records (day 365.125, 365.375)
VARS = ["t_bot", "sphum_bot", "p_surf", "u_bot", "flux_lw", "flux_sw",
        "lprec", "fprec", "coszen"]


def append_year(year):
    src_year = year + 1 if year < LAST else FIRST
    f_this = "%s/wfde5_atm_%d.nc" % (DST, year)
    f_next = "%s/wfde5_atm_%d.nc" % (DST, src_year)
    for f in (f_this, f_next):
        if not os.path.exists(f):
            print("  missing %s -- skip" % f)
            return False

    d = nc.Dataset(f_this, "a")
    n_before = len(d.variables["time"])
    s = nc.Dataset(f_next)
    t_base = float(d.variables["time"][NBASE - 1])      # day 364.875
    for k in range(NAPP):
        d.variables["time"][NBASE + k] = t_base + 0.25 * (k + 1)
        for v in VARS:
            d.variables[v][NBASE + k, :, :] = s.variables[v][k, :, :]
    s.close()
    t = d.variables["time"][:]
    print("  %d: %d -> %d records, last=%.3f (boundary from %d)" % (
        year, n_before, len(t), float(t[-1]), src_year))
    d.close()
    return True


if __name__ == "__main__":
    ok = 0
    for y in range(FIRST, LAST + 1):
        if append_year(y):
            ok += 1
    print("done: %d/%d years" % (ok, LAST - FIRST + 1))
