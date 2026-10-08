#!/usr/bin/env python3
"""Compare FMS clock tables of the offline speed-test runs (LM4 notes 13.71).

usage: python phentest_timing.py <ctrl_clock_table.txt> <exp1_clock_table.txt> [<exp2> ...]
Each file = the "Tabulating mpp_clock statistics" block of esm4p5.log (saved by phentest_pbs_chain.sh).
Columns: hits tmin tmax tavg tstd tfrac grain pemin pemax; the clock name is everything before them.
Prints, per clock of interest: tmin / tavg / tmax, PE imbalance (tmax-tmin)/tavg, and for each experiment the
speed-up (CTRL-EXP)/CTRL on tmax (what sets wall-clock) and on tavg.
"""
import os
import sys

CLOCKS = ["Total runtime", "Main loop", "Land", "Update-Land-Fast", "Update-Land-Slow", "land_tracer", "land_tracer:ddep",
          "SFC boundary layer", "Flux DN from atm", "Flux UP to atm", "Land-ice-atm coupler", "update_river", "Ice Fast"]


def parse(path):
    d = {}
    for ln in open(path):
        t = ln.split()
        if len(t) < 10:
            continue
        try:
            nums = [float(x) for x in t[-9:]]
        except ValueError:
            continue
        name = " ".join(t[:-9]).strip()
        d[name] = dict(hits=nums[0], tmin=nums[1], tmax=nums[2], tavg=nums[3], tfrac=nums[5])
    return d


runs = [(os.path.basename(os.path.dirname(os.path.abspath(p))) or p, parse(p)) for p in sys.argv[1:]]
ctrl = runs[0][1]
print("%-22s" % "clock", end="")
for nm, _ in runs:
    print(" | %-34s" % ("%s  tmin/tavg/tmax (s)  imb%%" % nm), end="")
print()
for c in CLOCKS:
    if c not in ctrl:
        continue
    print("%-22s" % c, end="")
    for nm, d in runs:
        if c in d:
            x = d[c]; imb = 100 * (x["tmax"] - x["tmin"]) / x["tavg"] if x["tavg"] > 0 else 0
            print(" | %8.0f/%8.0f/%8.0f %5.1f" % (x["tmin"], x["tavg"], x["tmax"], imb), end="")
        else:
            print(" | %-34s" % "absent", end="")
    print()
print("\nspeed-up vs %s = (CTRL-EXP)/CTRL x 100, on tmax (wall-clock) and on tavg" % runs[0][0])
for nm, d in runs[1:]:
    print("  %s:" % nm)
    for c in CLOCKS:
        if c in ctrl and c in d and ctrl[c]["tmax"] > 0:
            print("    %-22s tmax %+6.1f %%   tavg %+6.1f %%" % (c, 100 * (ctrl[c]["tmax"] - d[c]["tmax"]) / ctrl[c]["tmax"],
                                                               100 * (ctrl[c]["tavg"] - d[c]["tavg"]) / ctrl[c]["tavg"]))
        elif c in ctrl and c not in d:
            print("    %-22s removed (was %.0f s tavg)" % (c, ctrl[c]["tavg"]))
