#!/usr/bin/env python3
"""Compare two JULES spin-up cycles: (1) end-of-cycle states from the 2011-01-01
dumps, (2) same-year annual means from the monthly output.

Points used: non-ice land (frac of ice tile < 1) minus the perennial-snow mask
(jules_perennial_snow_mask_1deg.nc).  Means are cos(lat)-weighted.
Per-cell convergence = |X(cB) - X(cA)| / |X(cA)| <= 1 % per cycle.
usage: python spinup_cycle_compare.py <output_dir> <cycleA> <cycleB>
"""
import sys
import numpy as np
from netCDF4 import Dataset

d, ca, cb = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
rid = lambda c: 'jules_spinA_c%02d' % c
MASK = '/home/ydkoh/JULES_runs/ancil/global_1deg/jules_perennial_snow_mask_1deg.nc'
POOLS = ['DPM', 'RPM', 'BIO', 'HUM']


def dump(c):
    with Dataset('%s/%s.dump.20110101.0.nc' % (d, rid(c))) as f:
        f.set_auto_mask(False)
        g = {v: f.variables[v][:].astype('f8') for v in ('cs', 't_soil', 'sthuf', 'lai', 'canht', 'frac', 'snow_tile')}
        g['lat'] = f.variables['latitude'][:]; g['lon'] = f.variables['longitude'][:] % 360
    return g


A, B = dump(ca), dump(cb)
with Dataset(MASK) as m:
    snowm = m.variables['perennial_snow'][:] == 1
j = np.rint(A['lat'] + 89.5).astype(int); i = np.rint(A['lon']).astype(int) % 360
ice = A['frac'][-1] > 0.999
use = ~ice & ~snowm[j, i]
w = np.cos(np.deg2rad(A['lat']))
fp = A['frac'][:A['lai'].shape[0]]
print('points used %d (non-ice %d minus perennial snow %d)' % (use.sum(), (~ice).sum(), (snowm[j, i] & ~ice).sum()))


def stats(name, xa, xb):
    ok = use & np.isfinite(xa) & np.isfinite(xb)
    ma = (xa[ok] * w[ok]).sum() / w[ok].sum(); mb = (xb[ok] * w[ok]).sum() / w[ok].sum()
    rel = np.abs(xb - xa)[ok] / np.maximum(np.abs(xa[ok]), 1e-12)
    print('%-14s c%d %10.4g  c%d %10.4g  mean change %+8.3f %%  | cells <=1%% %5.1f %%  <=5%% %5.1f %%  median %.2f %%'
          % (name, ca, ma, cb, mb, 100 * (mb - ma) / ma, 100 * np.mean(rel <= 0.01), 100 * np.mean(rel <= 0.05),
             100 * np.median(rel)))


print('\n(1) end-of-cycle state, 2011-01-01 dumps')
for k, p in enumerate(POOLS):
    stats('cs ' + p, A['cs'][k].sum(0), B['cs'][k].sum(0))
stats('cs total', A['cs'].sum((0, 1)), B['cs'].sum((0, 1)))
pw = lambda g, v: np.nansum(g[v] * fp, 0) / np.maximum(fp.sum(0), 1e-12)
stats('lai (pft-wtd)', pw(A, 'lai'), pw(B, 'lai'))
stats('canht', pw(A, 'canht'), pw(B, 'canht'))
stats('sthuf col', A['sthuf'].mean(0), B['sthuf'].mean(0))
stats('t_soil deep', A['t_soil'][-1], B['t_soil'][-1])
ok = use
print('%-14s max |c%d - c%d| deep soil T = %.3f K' % ('', cb, ca, np.abs(B['t_soil'][-1] - A['t_soil'][-1])[ok].max()))
sn = snowm[j, i] & ~ice
print('perennial-snow cells: snow_tile max c%d %.0f, c%d %.0f kg/m2' % (ca, A['snow_tile'][:, sn].sum(0).max(), cb, B['snow_tile'][:, sn].sum(0).max()))

print('\n(2) same-year annual means, c%d minus c%d (land mean over used points)' % (cb, ca))
VARS = ['lai', 'cv', 'cs', 'gpp_gb', 'npp_gb', 'resp_s_gb', 'latent_heat', 'smc_tot', 't_soil', 't1p5m_gb']
yrs = [1981, 1982, 1985, 1990, 2000, 2010]
print('year ' + ' '.join('%10s' % v[:10] for v in VARS))
for y in yrs:
    row = []
    for c in (ca, cb):
        with Dataset('%s/%s.monthly.%d.nc' % (d, rid(c), y)) as f:
            f.set_auto_mask(False)
            fr = np.squeeze(f.variables['frac'][:]).astype('f8')
            o = {}
            for v in VARS:
                a = np.squeeze(f.variables[v][:]).astype('f8')
                if v == 'lai':
                    q = fr[:, :a.shape[1]]
                    a = np.nansum(a * q, 1) / np.maximum(q.sum(1), 1e-12)
                elif v == 't_soil':
                    a = a[:, -1]
                elif a.ndim > 2:
                    a = a.reshape(a.shape[0], -1, a.shape[-1]).sum(1)
                a = a.mean(0)
                ok = use & np.isfinite(a)
                o[v] = (a[ok] * w[ok]).sum() / w[ok].sum()
        row.append(o)
    print('%d ' % y + ' '.join('%+10.3g' % (row[1][v] - row[0][v]) for v in VARS))
