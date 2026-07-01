import numpy as np
from netCDF4 import Dataset
RST="/data2/ydkoh/lm4/RUN/lm4_spinup/RESTART"
import glob
fs=sorted(glob.glob(f"{RST}/19820101.000000.soil.res.tile*.nc"))
if not fs:
    print("아직 1982 restart 없음"); raise SystemExit
dT=[]
for f in fs:
    t=np.array(Dataset(f).variables["temp"][:],float)
    dT.append(t[-1][t[-1]<1e30])  # deepest layer
dTm=float(np.concatenate(dT).mean())
print(f"1982 deep soil T = {dTm:.2f} K  ->  {'WARM-START OK (~272.5)' if dTm<280 else 'COLD again (287)'}")
