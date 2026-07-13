#!/usr/bin/env python
# LM4 spin-up stability from land_annual (FMS-native ANNUAL MEANS; average_DT=365) -- proper
# means, comparable to CLM's annual mean, no rerun. Final 30-yr segment of 300-yr spin-up.
# Variables: soil water 0.70 m, soil temperature 1.20 m, column soil water, NEP (productivity).
# 6 tiles concatenated, unweighted land mean. soil_liq/ice are kg/m3 -> column = sum(rho*dz).
import glob
import numpy as np
from netCDF4 import Dataset

RUN = "/data2/ydkoh/lm4/RUN/lm4_spinup"
IWATER, ITEMP = 8, 10   # zfull nodes 0.70 m, 1.20 m

# layer thickness dz from zhalf_soil (land_static)
st = Dataset(sorted(glob.glob(f"{RUN}/*.land_static.tile1.nc"))[0])
zh = st.variables["zhalf_soil"][:].astype("f8").ravel() if "zhalf_soil" in st.variables else None
st.close()
if zh is not None and len(zh) >= 21:
    dz = np.diff(zh[:21])
else:  # fallback: midpoints of zfull
    zf = np.array([0.01,0.04,0.08,0.125,0.175,0.25,0.35,0.50,0.70,0.90,1.20,1.60,2.00,2.40,2.80,3.50,4.50,5.50,6.75,8.75])
    edges = np.concatenate([[0], (zf[:-1]+zf[1:])/2, [zf[-1]+(zf[-1]-zf[-2])/2]])
    dz = np.diff(edges)

def stack(var, tiles):
    return np.concatenate([tiles[t][var] for t in range(6)], axis=-1)   # (time,[lev,]cells)

tiles = []
for t in range(1, 7):
    d = Dataset(f"{RUN}/{{}}".format(sorted(__import__('os').listdir(RUN))[0]))  # placeholder
    d.close(); break
# load all tiles
T = {}
for t in range(1, 7):
    f = glob.glob(f"{RUN}/*.land_annual.tile{t}.nc")[0]
    d = Dataset(f); d.set_auto_mask(False)
    T[t-1] = {"soil_T": d.variables["soil_T"][:].astype("f8"),
              "sw": (d.variables["soil_liq"][:] + d.variables["soil_ice"][:]).astype("f8"),
              "nep": d.variables["nep"][:].astype("f8"),
              "time": d.variables["time"][:]}
    d.close()

nt = T[0]["soil_T"].shape[0]
def lm(a):
    a = a[np.abs(a) < 1e10]; return float(a.mean())

print("segyear,SW_070,ST_120,colwater,NEP")
for i in range(nt):
    sw = np.concatenate([T[t]["sw"][i, IWATER, :] for t in range(6)])
    stt = np.concatenate([T[t]["soil_T"][i, ITEMP, :] for t in range(6)])
    col = np.concatenate([np.nansum(np.where(np.abs(T[t]["sw"][i]) < 1e10,
              T[t]["sw"][i] * dz[:, None], np.nan), axis=0) for t in range(6)])
    nep = np.concatenate([T[t]["nep"][i, :] for t in range(6)])
    print("%d,%.5f,%.4f,%.3f,%.5f" % (i + 1, lm(sw), lm(stt), lm(col), lm(nep)))
