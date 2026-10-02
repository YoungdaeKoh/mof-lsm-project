#!/usr/bin/env python3
"""Where do JULES spin-up states still drift between two cycles?

Uses the 2011-01-01 dumps of cycles A and B (same points as spinup_cycle_compare.py:
non-ice land minus perennial-snow cells).  Unconverged = |dX|/|X_A| > 1 %.
Characterises soil moisture (column-mean sthuf) and HUM soil carbon drift by
latitude band, region, aridity (annual precip of cycle B's last year), permafrost
(deep soil T < 273.15 K), sign, and soil layer.
usage: python find_unconverged.py <output_dir> <cycleA> <cycleB>
"""
import sys
import numpy as np
from netCDF4 import Dataset

d, ca, cb = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
rid = lambda c: 'jules_spinA_c%02d' % c
MASK = '/home/ydkoh/JULES_runs/ancil/global_1deg/jules_perennial_snow_mask_1deg.nc'


def dump(c):
    with Dataset('%s/%s.dump.20110101.0.nc' % (d, rid(c))) as f:
        f.set_auto_mask(False)
        g = {v: f.variables[v][:].astype('f8') for v in ('cs', 't_soil', 'sthuf', 'frac', 'sm_sat')}
        g['lat'] = f.variables['latitude'][:]; g['lon'] = f.variables['longitude'][:] % 360
    return g


A, B = dump(ca), dump(cb)
lat, lon = A['lat'], A['lon']
with Dataset(MASK) as m:
    snowm = m.variables['perennial_snow'][:] == 1
j = np.rint(lat + 89.5).astype(int); i = np.rint(lon).astype(int) % 360
use = (A['frac'][-1] < 0.999) & ~snowm[j, i]
with Dataset('%s/%s.monthly.2010.nc' % (d, rid(cb))) as f:
    f.set_auto_mask(False)
    pr = np.squeeze(f.variables['precip'][:]).mean(0) * 86400 * 365       # mm/yr
permafrost = B['t_soil'][-1] < 273.15

regions = {'Sahara/Arabia': (lat > 12) & (lat < 35) & ((lon > 340) | (lon < 60)),
           'Australia': (lat < -10) & (lat > -45) & (lon > 110) & (lon < 155),
           'C. Asia/Gobi': (lat > 35) & (lat < 50) & (lon > 50) & (lon < 120),
           'Siberia': (lat > 50) & (lon > 60) & (lon < 180),
           'N. America boreal/Arctic': (lat > 50) & (lon > 190) & (lon < 300),
           'Amazon': (lat > -15) & (lat < 5) & (lon > 280) & (lon < 320),
           'S. Africa': (lat < -15) & (lon > 10) & (lon < 40),
           'SW USA/Mexico': (lat > 15) & (lat < 40) & (lon > 235) & (lon < 260)}


def report(name, xa, xb, layers=None):
    rel = (xb - xa) / np.maximum(np.abs(xa), 1e-12)
    bad = use & (np.abs(rel) > 0.01)
    n = bad.sum()
    print('\n== %s: unconverged %d of %d (%.1f %%) | drying/decreasing %d, wetting/increasing %d'
          % (name, n, use.sum(), 100 * n / use.sum(), (bad & (rel < 0)).sum(), (bad & (rel > 0)).sum()))
    bands = [(-60, -30), (-30, 0), (0, 30), (30, 60), (60, 90)]
    print('  lat band (unconverged / all used): ' + ', '.join(
        '%d..%d %d/%d' % (a, b, (bad & (lat >= a) & (lat < b)).sum(), (use & (lat >= a) & (lat < b)).sum()) for a, b in bands))
    print('  region: ' + ', '.join('%s %d' % (r, (bad & m).sum()) for r, m in regions.items()) +
          ', other %d' % (bad & ~np.any(list(regions.values()), axis=0)).sum())
    print('  annual precip of unconverged: median %.0f mm/yr (all used %.0f) | <250 mm/yr %d | permafrost %d (all used %d)'
          % (np.median(pr[bad]), np.median(pr[use]), (bad & (pr < 250)).sum(), (bad & permafrost).sum(), (use & permafrost).sum()))
    print('  |change| of unconverged: median %.1f %%, p95 %.1f %%, max %.1f %%'
          % (100 * np.median(np.abs(rel[bad])), 100 * np.percentile(np.abs(rel[bad]), 95), 100 * np.abs(rel[bad]).max()))
    if layers is not None:
        dl = np.abs(layers[1] - layers[0])[:, bad].mean(1)
        print('  mean |d sthuf| by soil layer (top->bottom) over unconverged: ' + ' '.join('%.4f' % x for x in dl))
    return bad


bsm = report('soil moisture (column-mean sthuf)', A['sthuf'].mean(0), B['sthuf'].mean(0), (A['sthuf'], B['sthuf']))
bhum = report('HUM soil carbon', A['cs'][3].sum(0), B['cs'][3].sum(0))
print('\noverlap soil-moisture & HUM unconverged: %d' % (bsm & bhum).sum())
dT = np.abs(B['t_soil'][-1] - A['t_soil'][-1]) * use
k = np.argsort(-dT)[:5]
print('largest deep soil T change: ' + ', '.join('(%.1f,%.1f) %.2f K' % (lat[p], lon[p], dT[p]) for p in k))
np.savez('%s/unconverged_c%d_c%d.npz' % (d, ca, cb), lat=lat, lon=lon, sm=bsm, hum=bhum, use=use)
