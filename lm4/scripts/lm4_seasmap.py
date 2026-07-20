# LM4 continuous spin-up: last-30yr (2251-2280) seasonal-mean per-cell fields for mapping.
# Seasons DJF/MAM/JJA/SON pooled by month. Keeps geolat_t/geolon_t per grid cell (C96, 6 tiles).
import glob, os
from datetime import datetime, timedelta
import numpy as np
from netCDF4 import Dataset

RUN = "/data2/ydkoh/lm4/RUN/lm4_wfde5_cont"
REF = datetime(1981, 1, 1)
Y0, Y1 = 2251, 2280   # spin-up yr 271-300 (last 30 = one full forcing cycle)
SEASON = {12:"DJF",1:"DJF",2:"DJF",3:"MAM",4:"MAM",5:"MAM",
          6:"JJA",7:"JJA",8:"JJA",9:"SON",10:"SON",11:"SON"}
SEAS = ["DJF","MAM","JJA","SON"]
VARS = ["soilT_top","soilT_deep","sens","evap","LAI"]

segs = sorted({os.path.basename(f).split(".land_month")[0]
               for f in glob.glob(f"{RUN}/*.land_month.tile1.nc")})

lat_all, lon_all = [], []
out = {v: {s: [] for s in SEAS} for v in VARS}

def getvars(nc):
    return {
        "soilT_top":  nc.variables["soil_T"][:, 0, :],
        "soilT_deep": nc.variables["soil_T"][:, 12, :],
        "sens":       nc.variables["sens"][:],
        "evap":       nc.variables["evap"][:],
        "LAI":        nc.variables["LAI"][:],
    }

for tile in range(1, 7):
    ncells = None
    ssum = {v: {s: None for s in SEAS} for v in VARS}
    scnt = {v: {s: None for s in SEAS} for v in VARS}
    glat = glon = None
    for seg in segs:
        nc = Dataset(f"{RUN}/{seg}.land_month.tile{tile}.nc")
        tv = nc.variables["time"][:]
        if len(tv) == 0:
            nc.close(); continue
        if glat is None:
            glat = nc.variables["geolat_t"][:]; glon = nc.variables["geolon_t"][:]
            ncells = len(glat)
            for v in VARS:
                for s in SEAS:
                    ssum[v][s] = np.zeros(ncells); scnt[v][s] = np.zeros(ncells)
        V = getvars(nc)
        for it, t in enumerate(tv):
            d = REF + timedelta(days=float(t))
            if not (Y0 <= d.year <= Y1):
                continue
            s = SEASON[d.month]
            for v in VARS:
                row = np.ma.masked_invalid(V[v][it])
                filled = row.filled(0.0); valid = (~np.ma.getmaskarray(row)).astype(float)
                ssum[v][s] += filled * valid
                scnt[v][s] += valid
        nc.close()
    lat_all.append(glat); lon_all.append(glon)
    for v in VARS:
        for s in SEAS:
            m = np.where(scnt[v][s] > 0, ssum[v][s] / np.maximum(scnt[v][s], 1), np.nan)
            out[v][s].append(m)

lat = np.concatenate(lat_all); lon = np.concatenate(lon_all)
save = {"lat": lat, "lon": lon}
for v in VARS:
    for s in SEAS:
        save[f"{v}_{s}"] = np.concatenate(out[v][s])
np.savez(f"{RUN}/seasmap_last30.npz", **save)
print(f"cells={len(lat)}  lat[{lat.min():.1f},{lat.max():.1f}]  lon[{lon.min():.1f},{lon.max():.1f}]")
print("window years", Y0, "-", Y1, "(spin-up yr 271-300)")
for v in VARS:
    jja = save[f"{v}_JJA"]; djf = save[f"{v}_DJF"]
    print(f"  {v:<11} JJA[{np.nanmin(jja):.3g},{np.nanmax(jja):.3g}] DJF[{np.nanmin(djf):.3g},{np.nanmax(djf):.3g}]")
print("NPZ:", f"{RUN}/seasmap_last30.npz")
