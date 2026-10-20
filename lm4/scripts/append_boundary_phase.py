"""Append the 2 next-year boundary records to WFDE5-phase LM4p forcing files (same job as the server's
append_boundary_1979_2024.py, which does it for the ramp-phase production set).

A run segment ends at Jan 1 03:00 of the next year while a converted file's last record is Dec 31 21:00
(day 364.875); records 1460-1461 (day 365.125, 365.375) are copied from the first two records of the next year's
file of the SAME phase variant. Overwrites only those two indices.
usage: python append_boundary_phase.py <suffix> <year> [<year> ...]   e.g.  _phasewfde5 2009 2010
"""
import os
import sys
import netCDF4 as nc

DST = "/data2/ydkoh/lm4/forcing_WFDE5_lm4p"
NBASE, NAPP = 1460, 2
VARS = ["t_bot", "sphum_bot", "p_surf", "u_bot", "flux_lw", "flux_sw", "lprec", "fprec", "coszen"]
SUF = sys.argv[1]
for year in map(int, sys.argv[2:]):
    f_this = "%s/wfde5_atm_%d%s.nc" % (DST, year, SUF)
    f_next = "%s/wfde5_atm_%d%s.nc" % (DST, year + 1, SUF)
    assert os.path.exists(f_this) and os.path.exists(f_next), "missing %s or %s" % (f_this, f_next)
    d = nc.Dataset(f_this, "a"); s = nc.Dataset(f_next)
    n0 = len(d.variables["time"]); t_base = float(d.variables["time"][NBASE - 1])
    for k in range(NAPP):
        d.variables["time"][NBASE + k] = t_base + 0.25 * (k + 1)
        for v in VARS:
            d.variables[v][NBASE + k, :, :] = s.variables[v][k, :, :]
    print("%d%s: %d -> %d records, last %.3f (boundary from %d)" % (year, SUF, n0, len(d.variables["time"]),
          float(d.variables["time"][-1]), year + 1))
    s.close(); d.close()
