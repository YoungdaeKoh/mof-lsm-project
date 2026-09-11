#!/usr/bin/env python
"""Is the chunked post-AD run the same as one continuous integration?

BATCH_SYSTEM is none on climate00, so CESM cannot resubmit itself and the spin-up
is driven in ten-year chunks from a shell, each chunk a fresh case.submit with
CONTINUE_RUN=TRUE.  The official CLM recipe chains with RESUBMIT instead.  The two
are supposed to be identical -- a restart continuation is exact -- but "supposed to"
is not evidence, and a broken chunk boundary would not crash, it would quietly
restart the forcing or reset a state and leave a step in the time series.

So: look for steps, and look for them at the right years.  Two different kinds of
boundary sit in this run and they must not be confused:

  chunk boundaries    model years 0093, 0102, 0112 -- where the shell stopped and
                      resubmitted.  A step here means the chaining is broken.
  forcing wrap        model years 0091, 0121 -- where GSWP3 cycling runs off 2010
                      and restarts at 1981.  A step here is expected and is not
                      our doing; see lsm-cyclic-forcing-wrap-shock.

The test variable is TWS, total water storage: fast enough to respond within a year
(unlike soil carbon, which would smear any step over decades) but integrated deeply
enough not to be pure weather noise.  The figure of merit is each year's jump
against the spread of jumps in the surrounding years -- a boundary that is no
different from its neighbours is a boundary that did nothing.

Run on climate00:
  /home/ydkoh/anaconda3/bin/python verify_chunk_continuity.py
"""

import glob
import os
import re

import numpy as np
import netCDF4 as nc

ARCH = "/home/ydkoh/CESM/spinup_raw/clm5_BGC_PAD"
VAR = "TWS"
Y0, Y1 = 80, 111                 # enough years either side of 0091/0093/0102
CHUNK_EDGES = [93, 102, 112]     # shell resubmitted here
WRAP_EDGES = [91, 121]           # GSWP3 cycling wrapped here

files = sorted(glob.glob("%s/*.clm2.h0.*.nc" % ARCH))
years = np.array([int(re.search(r"h0\.(\d{4})-", os.path.basename(f)).group(1))
                  for f in files])

with nc.Dataset(files[0]) as d:
    area = np.array(d.variables["area"][:], "f8")
    landfrac = np.array(d.variables["landfrac"][:], "f8")
W = area * np.where(np.isfinite(landfrac), landfrac, 0.0)

ann, got = [], []
for y in range(Y0, Y1 + 1):
    sel = [f for f, yy in zip(files, years) if yy == y]
    if len(sel) != 12:
        continue
    acc = None
    for f in sel:
        with nc.Dataset(f) as d:
            a = np.ma.filled(d.variables[VAR][0].astype("f8"), np.nan)
        acc = a if acc is None else acc + a
    a = acc / 12.0
    m = np.isfinite(a)
    ann.append(float((a[m] * W[m]).sum() / W[m].sum()))
    got.append(y)

ann = np.array(ann)
got = np.array(got)
jump = np.diff(ann)                       # jump[i] is the step into got[i+1]
jyear = got[1:]

# Spread of the steps that are not at any boundary -- the ordinary year-to-year
# wobble this run has anyway.  A boundary only counts as a break if it stands out
# against this.
plain = np.array([j for j, y in zip(jump, jyear)
                  if y not in CHUNK_EDGES and y not in WRAP_EDGES])
sd = plain.std()

print("%s annual global land mean, area-weighted  (mm)" % VAR)
print("background year-to-year step: mean %+.3f, sd %.3f (n=%d, boundaries excluded)\n"
      % (plain.mean(), sd, plain.size))
print("%-6s %12s %10s %8s   %s" % ("year", "value", "step", "step/sd", "boundary"))
for y, v in zip(got, ann):
    if y == got[0]:
        print("%-6d %12.2f %10s %8s" % (y, v, "-", "-"))
        continue
    j = jump[list(jyear).index(y)]
    tag = ""
    if y in CHUNK_EDGES:
        tag = "<-- CHUNK (shell resubmit)"
    elif y in WRAP_EDGES:
        tag = "<-- forcing wrap (expected)"
    print("%-6d %12.2f %+10.3f %8.1f   %s" % (y, v, j, j / sd if sd else 0, tag))

print()
for y in CHUNK_EDGES:
    if y in jyear:
        j = jump[list(jyear).index(y)]
        z = abs(j) / sd if sd else 0
        verdict = ("indistinguishable from an ordinary year"
                   if z <= 2 else "STANDS OUT -- chaining suspect")
        print("chunk boundary %04d: step %+.3f mm = %.1f sd -> %s" % (y, j, z, verdict))
print("\nA chunk boundary within ~2 sd of the ordinary year-to-year step means the")
print("shell chain left no trace, i.e. it behaved as one continuous integration.")
