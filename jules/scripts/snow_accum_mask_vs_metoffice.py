#!/usr/bin/env python3
"""(1) Is the Met Office WFD-EI frac (no coordinate variables) on the same index
layout as Chanhyuk's frac.nc (which has lat/lon)?  (2) How does it classify the
159 snow-accumulating 1-deg cells?  (3) Write the perpetual-snow mask.

The accumulating cells come from find_snow_accum.py (npz).  Mask file is on the
JULES 1-deg grid (lat -89.5..89.5, lon 0..359), like the forcing-gap mask.
"""
import numpy as np
from netCDF4 import Dataset

A = '/data1/backup/ChanhyukChoi/002.JULES_RUN/JULES/ancil/'
NPZ = '/data2/ydkoh/JULES_runs/spinup_A_trifeq/output/snow_accum_jules_spinA_c01.npz'
OUT = '/home/ydkoh/JULES_runs/ancil/global_1deg/jules_perennial_snow_mask_1deg.nc'


def read(path):
    with Dataset(path) as f:
        f.set_auto_mask(False)
        a = f.variables['field1391'][:].astype('f8')
        lat = f.variables['lat'][:] if 'lat' in f.variables else None
        lon = f.variables['lon'][:] if 'lon' in f.variables else None
    a[np.abs(a) > 1e19] = np.nan
    return a, lat, lon


ch, lat, lon = read(A + 'frac.nc')
mo, _, _ = read(A + 'from_metoffice/qrparm.veg.frac2d.nc')
print('chanhyuk frac.nc: lat %.2f..%.2f, lon %.2f..%.2f' % (lat[0], lat[-1], lon[0], lon[-1]))
both = np.isfinite(ch) & np.isfinite(mo)
print('index-space comparison: land masks equal %s | identical values %.4f of common cells | max|diff| %.3g'
      % (np.array_equal(np.isfinite(ch[8]), np.isfinite(mo[8])), np.mean(ch[both] == mo[both]),
         np.nanmax(np.abs(ch - mo))))
# also test the flipped / rolled layouts, to be sure the match is not accidental
for name, m in (('lat-flipped', mo[:, ::-1]), ('lon-rolled 180', np.roll(mo, 360, axis=2))):
    b2 = np.isfinite(ch) & np.isfinite(m)
    print('  %-15s identical %.4f' % (name, np.mean(ch[b2] == m[b2]) if b2.any() else 0))

# put both on 0..360 lon order, ascending lat (as make_grid_info_1deg.py does)
k = int(np.argmin(np.abs(lon - 0.25)))
if lat[0] > lat[-1]:
    ch, mo = ch[:, ::-1], mo[:, ::-1]
ch, mo = np.roll(ch, -k, axis=2), np.roll(mo, -k, axis=2)

z = np.load(NPZ)
acc = z['acc']
j = np.rint(z['lat'] + 89.5).astype(int); i = np.rint(z['lon']).astype(int) % 360
jj, ii = j[acc], i[acc]
def blk(a, t):                       # ice fraction of the four 0.5 deg sub-cells of each cell
    s = np.stack([a[t, 2 * jj + p, 2 * ii + q] for p in (0, 1) for q in (0, 1)], 1)
    return s
ice_mo, ice_ch = blk(mo, 8), blk(ch, 8)
print('\n159 accumulating cells, ice tile of the four 0.5 deg sub-cells:')
print('  Met Office: sub-cells ice>0: %d of %d | cells with any ice sub-cell %d | cells with ice block mean >= 0.5 %d'
      % ((np.nan_to_num(ice_mo) > 0).sum(), ice_mo.size, (np.nan_to_num(ice_mo) > 0).any(1).sum(),
         (np.nanmean(ice_mo, 1) >= 0.5).sum()))
print('  Chanhyuk  : sub-cells ice>0: %d of %d | cells with any ice sub-cell %d'
      % ((np.nan_to_num(ice_ch) > 0).sum(), ice_ch.size, (np.nan_to_num(ice_ch) > 0).any(1).sum()))
# dominant non-ice tile in the Met Office source for those cells
dom = np.nanmean(np.stack([blk(mo, t) for t in range(9)]), axis=2).argmax(0)
names = ['BT', 'NT', 'C3', 'C4', 'SH', 'urban', 'lake', 'bare', 'ice']
print('  Met Office dominant tile: ' + ', '.join('%s %d' % (names[t], (dom == t).sum()) for t in range(9) if (dom == t).any()))

# mask file
m = np.zeros((180, 360), 'i1'); m[jj, ii] = 1
rise = np.full((180, 360), -1.0, 'f4'); rise[jj, ii] = z['rise'][acc]
with Dataset(OUT, 'w', format='NETCDF4_CLASSIC') as o:
    o.createDimension('lat', 180); o.createDimension('lon', 360)
    v = o.createVariable('lat', 'f8', ('lat',)); v[:] = -89.5 + np.arange(180); v.units = 'degrees_north'
    v = o.createVariable('lon', 'f8', ('lon',)); v[:] = np.arange(360.0); v.units = 'degrees_east'
    v = o.createVariable('perennial_snow', 'i1', ('lat', 'lon')); v[:] = m
    v.long_name = 'non-ice JULES land cell with unbounded snow accumulation (spin-up A cycle 1); exclude from convergence/snow diagnostics'
    v = o.createVariable('snow_rise', 'f4', ('lat', 'lon'), fill_value=-1.0); v[:] = rise
    v.long_name = 'snow_mass rise, last minus first 5-yr mean, 1983-2009'; v.units = 'kg m-2'
    o.source = 'jules/scripts/find_snow_accum.py + snow_accum_mask_vs_metoffice.py'
print('\nwrote %s (%d cells)' % (OUT, m.sum()))
