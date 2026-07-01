#!/usr/bin/env python
# Build an HRLDAS gridded SETUP file from a WPS geo_em.d01.nc (cold start).
# Renames geo_em static fields to HRLDAS names + adds cold-start initial state.
# Usage: python geoem_to_hrldas_setup.py geo_em.d01.nc HRLDAS_setup_out.nc
import sys
import numpy as np
from netCDF4 import Dataset

geoem, outpath = sys.argv[1], sys.argv[2]
g = Dataset(geoem)
ny = g.dimensions["south_north"].size
nx = g.dimensions["west_east"].size

xlat = g.variables["XLAT_M"][0]
xlon = g.variables["XLONG_M"][0]
lu = np.rint(g.variables["LU_INDEX"][0]).astype("i4")
sct = np.rint(g.variables["SCT_DOM"][0]).astype("i4")
hgt = g.variables["HGT_M"][0]
landmask = g.variables["LANDMASK"][0]
soiltemp = g.variables["SOILTEMP"][0]
green = g.variables["GREENFRAC"][0]            # (month, ny, nx)
lai12 = g.variables["LAI12M"][0]               # (month, ny, nx)

# deep soil / skin temperature: use SOILTEMP over land, fill ocean (SOILTEMP~0) with 285 K
tmn = np.where(soiltemp > 150.0, soiltemp, 285.0).astype("f4")
shdmax = (green.max(axis=0) * 100.0).astype("f4")
shdmin = (green.min(axis=0) * 100.0).astype("f4")
lai = lai12.mean(axis=0).astype("f4")
xland = np.where(landmask >= 0.5, 1, 2).astype("i4")   # 1=land/ice, 2=water

# geogrid dominant soil category is 14 (water) over ~1/3 of land cells at 0.5deg
# (lakes/coasts/high-lat). Noah-MP internally resets these to sandy clay loam (7)
# and PRINTS a warning every timestep -> multi-GB log runaway that fills disk and
# kills long runs. Pre-assign them to 7 here so the reset (and the print) never fires.
sct = np.where((landmask >= 0.5) & (sct == 14), 7, sct).astype("i4")

# 4-layer Noah soil config (matches namelist soil_thick_input)
dzs = np.array([0.10, 0.30, 0.60, 1.00], dtype="f4")
zs = np.array([0.05, 0.25, 0.70, 1.50], dtype="f4")     # layer node (center) depths
nsoil = 4

o = Dataset(outpath, "w", format="NETCDF4")
o.createDimension("west_east", nx)
o.createDimension("south_north", ny)
o.createDimension("soil_layers_stag", nsoil)
o.createDimension("Time", None)


def w2d(name, arr, dtype, units, desc):
    v = o.createVariable(name, dtype, ("Time", "south_north", "west_east"))
    v.units = units
    v.description = desc
    v[0, :, :] = arr


w2d("XLAT", xlat, "f4", "degrees_north", "latitude")
w2d("XLONG", xlon, "f4", "degrees_east", "longitude")
w2d("TMN", tmn, "f4", "K", "soil temperature lower boundary")
w2d("HGT", hgt, "f4", "m", "elevation")
w2d("SEAICE", np.zeros((ny, nx), "f4"), "f4", "-", "sea ice fraction")
w2d("SHDMAX", shdmax, "f4", "%", "maximum annual vegetation cover")
w2d("SHDMIN", shdmin, "f4", "%", "minimum annual vegetation cover")
w2d("LAI", lai, "f4", "m2/m2", "leaf area index")
w2d("XLAND", xland, "i4", "-", "land mask: 1=land/ice 2=water")
w2d("IVGTYP", lu, "i4", "-", "vegetation type")
w2d("ISLTYP", sct, "i4", "-", "soil texture type")
w2d("SNOW", np.zeros((ny, nx), "f4"), "f4", "mm", "snow water equivalent")
w2d("SNODEP", np.zeros((ny, nx), "f4"), "f4", "m", "snow depth")
w2d("CANWAT", np.zeros((ny, nx), "f4"), "f4", "mm", "canopy surface water")
w2d("TSK", tmn, "f4", "K", "surface skin temperature")

vd = o.createVariable("DZS", "f4", ("Time", "soil_layers_stag"))
vd.units = "m"; vd.description = "soil layer thicknesses"; vd[0, :] = dzs
vz = o.createVariable("ZS", "f4", ("Time", "soil_layers_stag"))
vz.units = "m"; vz.description = "soil node depths"; vz[0, :] = zs

vt = o.createVariable("TSLB", "f4", ("Time", "soil_layers_stag", "south_north", "west_east"))
vt.units = "K"; vt.description = "soil temperature"
vs = o.createVariable("SMOIS", "f4", ("Time", "soil_layers_stag", "south_north", "west_east"))
vs.units = "m3/m3"; vs.description = "volumetric soil moisture"
for k in range(nsoil):
    vt[0, k, :, :] = tmn               # cold start: all layers = deep soil temp
    vs[0, k, :, :] = 0.30              # cold start: uniform 0.3 m3/m3

# global attributes (HRLDAS read_hrldas_hdrinfo requires all of these)
copy_attrs = ["DX", "DY", "MAP_PROJ", "MMINLU", "ISWATER", "ISICE", "ISURBAN"]
for a in copy_attrs:
    o.setncattr(a, g.getncattr(a))
# attrs that may be absent in geo_em for lat-lon -> default to 0
for a, default in [("TRUELAT1", 0.0), ("TRUELAT2", 0.0), ("STAND_LON", 0.0)]:
    o.setncattr(a, g.getncattr(a) if a in g.ncattrs() else np.float32(default))
o.GRID_ID = np.int32(1)
if "ISLAKE" in g.ncattrs():
    o.setncattr("ISLAKE", g.getncattr("ISLAKE"))
o.TITLE = "HRLDAS gridded setup (cold start) from geo_em via geoem_to_hrldas_setup.py"
o.close()
print("wrote %s  (%dx%d, land cells=%d)" % (outpath, ny, nx, int((landmask >= 0.5).sum())))
