#!/usr/bin/env python3
"""Write the mask of JULES 1-deg land cells whose WFDE5 forcing is nearest-neighbour filled.

JULES land (land_fraction > 0, notes 13) and WFDE5 disagree on coasts and islands;
wfde5_nnfill_1deg.sh fills those cells from the nearest valid WFDE5 cell.  This file
records which cells were filled and how far the value came from, so analyses can
drop them (e.g. nn_dist_deg > 1 = remote islands on far-away weather).
Grid = grid_info_1deg.nc (lat -89.5..89.5 ascending, lon 0..359).
"""
import numpy as np
from netCDF4 import Dataset

GI = '/home/ydkoh/JULES_runs/ancil/global_1deg/grid_info_1deg.nc'
SRC = '/data2/ydkoh/jules_wfde5_1deg/wfde5_1deg_1981.nc'   # unfilled CDO remap
OUT = '/data2/ydkoh/jules_wfde5_1deg_nnfill/jules_wfde5_gapcells_1deg.nc'

with Dataset(GI) as g:
    g.set_auto_mask(False)
    land = g.variables['land_fraction'][:] > 0
    lat, lon = g.variables['lat'][:], g.variables['lon'][:]
with Dataset(SRC) as f:
    f.set_auto_mask(False)
    assert np.allclose(f.variables['lat'][:], lat) and np.allclose(f.variables['lon'][:], lon)
    miss = np.abs(f.variables['TBOT'][0]) > 1e19       # mask is constant in time (checked)
gap = miss & land

# great-circle distance to the nearest originally valid cell
LA, LO = np.meshgrid(np.deg2rad(lat), np.deg2rad(lon), indexing='ij')
vj, vi = np.where(~miss)
dist = np.full(land.shape, -1.0, dtype='f4')
for j, i in zip(*np.where(gap)):
    c = (np.sin(LA[j, i]) * np.sin(LA[vj, vi]) +
         np.cos(LA[j, i]) * np.cos(LA[vj, vi]) * np.cos(LO[j, i] - LO[vj, vi]))
    dist[j, i] = np.rad2deg(np.arccos(np.clip(c, -1, 1))).min()

with Dataset(OUT, 'w', format='NETCDF4_CLASSIC') as o:
    o.createDimension('lat', lat.size)
    o.createDimension('lon', lon.size)
    v = o.createVariable('lat', 'f8', ('lat',)); v[:] = lat; v.units = 'degrees_north'
    v = o.createVariable('lon', 'f8', ('lon',)); v[:] = lon; v.units = 'degrees_east'
    v = o.createVariable('gap', 'i1', ('lat', 'lon'))
    v[:] = gap.astype('i1')
    v.long_name = 'JULES land cell with nearest-neighbour filled WFDE5 forcing (1=yes)'
    v = o.createVariable('nn_dist_deg', 'f4', ('lat', 'lon'), fill_value=-1.0)
    v[:] = dist
    v.long_name = 'great-circle distance to nearest valid WFDE5 1-deg cell'
    v.units = 'degree'
    o.source = 'jules/scripts/make_wfde5_gapmask_1deg.py'

d = dist[gap]
print('gap cells %d (of %d land) | dist <=1 deg %d, 1-10 %d, >10 %d | max %.1f' % (
    gap.sum(), land.sum(), (d <= 1).sum(), ((d > 1) & (d <= 10)).sum(), (d > 10).sum(), d.max()))
print('wrote', OUT)
