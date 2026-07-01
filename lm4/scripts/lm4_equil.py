#!/usr/bin/env python3
# Spin-up equilibrium check: annual land-mean deep soil T and column soil water
# from yearly LM4 soil.res restarts (all 6 tiles combined, unweighted land mean).
import glob, os, re
import numpy as np
from netCDF4 import Dataset

RST = "/data2/ydkoh/lm4/RUN/lm4_spinup/RESTART"
years = sorted({m.group(1)
                for f in os.listdir(RST) if "soil.res.tile1" in f
                for m in [re.match(r"(\d{4})", f)] if m})

print(f"{'year':>6} {'deepT_K':>10} {'colWater_kg/m2':>16}")
prevT = prevW = None
for y in years:
    dT, wsum, npt = [], [], 0
    for t in range(1, 7):
        fp = f"{RST}/{y}0101.000000.soil.res.tile{t}.nc"
        if not os.path.exists(fp):
            continue
        nc = Dataset(fp)
        temp = nc.variables["temp"][:]          # (zfull, tile_index)
        wl = nc.variables["wl"][:]
        ws = nc.variables["ws"][:]
        fv = nc.variables["temp"]._FillValue
        temp = np.ma.masked_greater(temp, 1e30)
        wl = np.ma.masked_greater(wl, 1e30)
        ws = np.ma.masked_greater(ws, 1e30)
        dT.append(temp[-1, :])                  # deepest layer T per land point
        wsum.append((wl + ws).sum(axis=0))      # column total water per land point
        nc.close()
    dTall = np.ma.concatenate(dT)
    wall = np.ma.concatenate(wsum)
    mT = float(dTall.mean()); mW = float(wall.mean())
    dt = f"{mT-prevT:+.4f}" if prevT is not None else "  --"
    dw = f"{mW-prevW:+.3f}" if prevW is not None else "  --"
    print(f"{y:>6} {mT:>10.4f} {mW:>16.3f}   dT={dt} dW={dw}")
    prevT, prevW = mT, mW
