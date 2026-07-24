"""Per-species (PFT) JJA LAI on C96 land points, 1982, + coords.

lai_by_species is (time, species=7, grid_index); JJA mean gives each PFT's leaf
area index per cell. The PFT share of a cell/region = lai_species / total_lai.
Coords recovered from land_static grid_index (same land mask as by_species).
"""
import numpy as np
from netCDF4 import Dataset, num2date

RUN = "/data2/ydkoh/lm4/RUN/lm4_spinup30"
ARCH = RUN + "/archive/y1982"
INP = RUN + "/INPUT"
NX = 96
FILL = 1e30
SPECIES = ["prioria", "picea", "larix", "acer", "c4grass", "c3grass", "default"]

lat_all, lon_all, lai_all = [], [], []
for t in range(1, 7):
    st = Dataset("%s/19820101.land_static.tile%d.nc" % (ARCH, t))
    gi_static = st.variables["grid_index"][:].astype(int)
    st.close()
    g = Dataset("%s/C96_grid.tile%d.nc" % (INP, t))
    X = g.variables["x"][:]; Y = g.variables["y"][:]; g.close()

    d = Dataset("%s/19820101.land_month_by_species.tile%d.nc" % (ARCH, t))
    gi = d.variables["grid_index"][:].astype(int)
    tv = d.variables["time"]
    months = np.array([dt.month for dt in
                       num2date(tv[:], tv.units, getattr(tv, "calendar", "noleap"))])
    jja = np.isin(months, [6, 7, 8])
    lai = np.ma.filled(d.variables["lai"][:].astype("f8"), np.nan)  # (t,7,ncell)
    lai[np.abs(lai) > FILL] = np.nan
    lai_jja = np.nanmean(lai[jja], axis=0)                          # (7, ncell)
    d.close()

    # coords from THIS stream's own grid_index (guarantees alignment)
    j = gi // NX; i = gi % NX
    lat_all.append(Y[2 * j + 1, 2 * i + 1])
    lon_all.append(X[2 * j + 1, 2 * i + 1])
    lai_all.append(lai_jja)

lat = np.concatenate(lat_all)
lon = np.concatenate(lon_all)
lon = np.where(lon > 180, lon - 360, lon)
lai = np.concatenate(lai_all, axis=1)            # (7, npoints)

np.savez(RUN + "/lm4_pft_jja1982.npz", lat=lat, lon=lon, lai_sp=lai,
         species=np.array(SPECIES))
tot = np.nansum(lai, axis=0)
print("points=%d  total-LAI mean=%.3f" % (len(lat), np.nanmean(tot)))
print("global PFT share of total leaf area:")
share = np.nansum(lai, axis=1) / np.nansum(tot)
for s, f in zip(SPECIES, share):
    print("  %-8s %.1f%%" % (s, 100 * f))
