#!/usr/bin/env python3
# LAI map extract: geographic coords from cpl.hi.lnd (lndExp_lon/lat, valid),
# LAI from land_annual (compressed grid_index, compress="grid_yt grid_xt", nx=96).
import glob
import numpy as np
from netCDF4 import Dataset

RD = "/data2/ydkoh/lm4/RUN/lm4_spinup"
NX = 96

# geographic coords (6, ny, nx) from a coupler-history file
chf = sorted(glob.glob(f"{RD}/ufs.cpld.cpl.hi.lnd.*.nc"))[0]
c = Dataset(chf)
LON = np.array(c.variables["lndExp_lon"][0])   # (ntile, ny, nx)
LAT = np.array(c.variables["lndExp_lat"][0])
c.close()
print("coord file:", chf.split("/")[-1], "shape", LON.shape,
      "lon", LON.min(), LON.max(), "lat", LAT.min(), LAT.max())

lon, lat, lai = [], [], []
for t in range(1, 7):
    nc = Dataset(f"{RD}/19810101.land_annual.tile{t}.nc")
    gi = np.array(nc.variables["grid_index"][:]).astype(int)   # compressed positions
    L = np.array(nc.variables["LAI"][:], float)[-1]            # last annual record
    nc.close()
    j = gi // NX; i = gi % NX
    glon = LON[t-1, j, i]; glat = LAT[t-1, j, i]
    good = (L < 1e30) & np.isfinite(L)
    lon.append(glon[good]); lat.append(glat[good]); lai.append(L[good])
lon = np.concatenate(lon); lat = np.concatenate(lat); lai = np.concatenate(lai)
print("npts", lon.size, "lon", lon.min(), lon.max(), "lat", lat.min(), lat.max(),
      "LAI mean", round(float(lai.mean()), 3))
np.savez("/data2/ydkoh/lm4/lai_map_data.npz", lon=lon, lat=lat, lai=lai)
print("saved")
