# Recover real C96 cell-center lat/lon from grid_index (CF compress "grid_yt grid_xt")
# + C96_grid supergrid centers. Merge into the seasonal-map npz (values already correct).
import numpy as np
from netCDF4 import Dataset
RUN = "/data2/ydkoh/lm4/RUN/lm4_wfde5_cont"
NX = 96
lat_all, lon_all = [], []
for tile in range(1, 7):
    st = Dataset(f"{RUN}/19810101.land_static.tile{tile}.nc")
    gi = st.variables["grid_index"][:].astype(int); st.close()
    g = Dataset(f"{RUN}/INPUT/C96_grid.tile{tile}.nc")
    X = g.variables["x"][:]; Y = g.variables["y"][:]; g.close()   # (193,193) supergrid
    j = gi // NX; i = gi % NX                                     # 0-based cell (j,i)
    lat = Y[2*j + 1, 2*i + 1]; lon = X[2*j + 1, 2*i + 1]          # cell centers
    lat_all.append(lat); lon_all.append(lon)
lat = np.concatenate(lat_all); lon = np.concatenate(lon_all)
lon = np.where(lon > 180, lon - 360, lon)   # -> [-180,180] for plotting
# merge into existing npz
d = dict(np.load(f"{RUN}/seasmap_last30.npz"))
d["lat"] = lat; d["lon"] = lon
np.savez(f"{RUN}/seasmap_last30.npz", **d)
print(f"cells={len(lat)}  lat[{lat.min():.2f},{lat.max():.2f}]  lon[{lon.min():.2f},{lon.max():.2f}]")
# quick sanity: latitudinal spread of a field
jja = d["soilT_top_JJA"]
for band,(a,b) in {"NH high":(60,90),"tropics":(-15,15),"SH high":(-90,-60)}.items():
    m=(lat>=a)&(lat<b); 
    if m.sum(): print(f"  soilT_top JJA {band}: {np.nanmean(jja[m]):.1f} K (n={m.sum()})")
