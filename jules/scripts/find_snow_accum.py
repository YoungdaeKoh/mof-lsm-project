#!/usr/bin/env python3
"""Which JULES 1-deg land points keep accumulating snow through a spin-up cycle,
and are they the cells the 0.5 -> 1 deg ice handling touched?

Accumulating = the summer minimum (lowest monthly mean) of snow_mass is > 0 in
every one of the last 10 years AND the annual mean rose by > THR kg/m2 between
the first and last 5-year blocks after the 1982 equilibrium jump.
Ice classes come from the 0.5 deg frac ancil (ice tile = 9th, 2x2 block of
0.5 deg sub-cells under each 1 deg cell, lon rolled to 0..360 as in
make_grid_info_1deg.py):
  pure-ice  : excluded already (ice tile frac == 1 at 1 deg)
  cleaned   : 0 < block ice < 0.5 -> ice removed by the majority rule
  no-ice    : no 0.5 deg sub-cell is ice
usage: python find_snow_accum.py <output_dir> <run_id> <y0> <y1>
"""
import sys
import numpy as np
from netCDF4 import Dataset

d, rid, y0, y1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
THR = 10.0        # kg/m2 rise between first and last 5-yr blocks
F05 = '/data1/backup/ChanhyukChoi/002.JULES_RUN/JULES/ancil/frac.nc'
GAP = '/data2/ydkoh/jules_wfde5_1deg_nnfill/jules_wfde5_gapcells_1deg.nc'

ann, amin = [], []
for y in range(y0, y1 + 1):
    with Dataset('%s/%s.monthly.%d.nc' % (d, rid, y)) as f:
        f.set_auto_mask(False)
        s = np.squeeze(f.variables['snow_mass_gb'][:]).astype('f8')   # (12, np)
        if y == y0:
            lat = np.squeeze(f.variables['latitude'][:])
            lon = np.squeeze(f.variables['longitude'][:]) % 360
            frac = np.squeeze(f.variables['frac'][0]).astype('f8')
    ann.append(s.mean(0)); amin.append(s.min(0))
ann, amin = np.array(ann), np.array(amin)
ice1 = frac[-1] > 0.999
first = ann[:5].mean(0); last = ann[-5:].mean(0)
perennial = (amin[-10:] > 0).all(0)
acc = perennial & (last - first > THR) & ~ice1
w = np.cos(np.deg2rad(lat)) * ~ice1

# 0.5 deg ice fraction per 1 deg block
with Dataset(F05) as g:
    g.set_auto_mask(False)
    lon05 = g.variables['lon'][:]
    ice05 = g.variables['field1391'][8].astype('f8')                     # (360, 720)
    lat05 = g.variables['lat'][:]
ice05[np.abs(ice05) > 1e19] = 0.0
if lat05[0] > lat05[-1]:
    ice05 = ice05[::-1]
k = int(np.argmin(np.abs(lon05 - 0.25)))                                 # roll so lon starts at 0.25
ice05 = np.roll(ice05, -k, axis=1)
blk = ice05.reshape(180, 2, 360, 2).mean(axis=(1, 3))                    # 1 deg block mean
nsub = (ice05 > 0).reshape(180, 2, 360, 2).sum(axis=(1, 3))
j = np.rint(lat + 89.5).astype(int); i = np.rint(lon).astype(int) % 360
b, n = blk[j, i], nsub[j, i]
cleaned = (b > 0) & (b < 0.5) & ~ice1
with Dataset(GAP) as g:
    gap = (g.variables['gap'][:] == 1)[j, i]

trend_all = (last - first) / (y1 - y0 - 4)
share = (trend_all[acc] * w[acc]).sum() / (trend_all * w).sum()
print('%s %d-%d: non-ice land %d | accumulating %d | their share of the land-mean snow rise %.0f %%'
      % (rid, y0, y1, int((~ice1).sum()), int(acc.sum()), 100 * share))
print('  of accumulating: ice-cleaned (0<ice05<0.5) %d | any 0.5deg ice sub-cell %d | no 0.5deg ice %d | forcing-gap filled %d'
      % ((acc & cleaned).sum(), (acc & (n > 0)).sum(), (acc & (n == 0)).sum(), (acc & gap).sum()))
print('  ice-cleaned cells total %d, of which accumulating %d' % (cleaned.sum(), (acc & cleaned).sum()))
regions = {'Greenland': (lat > 58) & (lon > 285) & (lon < 350),
           'Arctic isl. (>70N, not GL)': (lat > 70) & ~((lon > 285) & (lon < 350)),
           'HMA/Tibet': (lat > 25) & (lat < 46) & (lon > 65) & (lon < 105),
           'Alaska/Yukon': (lat > 55) & (lon > 190) & (lon < 230),
           'Andes/Patagonia': (lat < 0) & (lon > 280) & (lon < 300),
           'Iceland/Scandinavia/Alps': (lat > 43) & ((lon < 35) | (lon > 335))}
print('  by region: ' + ', '.join('%s %d' % (r, (acc & m).sum()) for r, m in regions.items()))
o = np.argsort(-(last - first) * acc)[:15]
print('  top 15 (lat, lon, rise kg/m2, summer-min last yr, ice05 block, 0.5deg ice sub-cells, gap):')
for p in o:
    if acc[p]:
        print('   %6.1f %6.1f  %8.0f  %8.0f   %.2f  %d  %s' % (lat[p], lon[p], last[p] - first[p], amin[-1, p], b[p], n[p], gap[p]))
np.savez('%s/snow_accum_%s.npz' % (d, rid), lat=lat, lon=lon, acc=acc, rise=last - first, ice05=b, nsub=n)
