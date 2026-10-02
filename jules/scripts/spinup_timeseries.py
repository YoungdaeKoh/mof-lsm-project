#!/usr/bin/env python3
"""Annual land-mean time series of a JULES 1-deg spin-up cycle.

Land mean = cos(lat)-weighted over non-ice land points (pure-ice points, frac of
the ice tile == 1, are excluded as for the other models' convergence checks),
minus the perennial-snow cells (jules_perennial_snow_mask_1deg.nc) when that
mask exists.  snow_max_mask = largest annual-mean snow_mass over those cells.
PFT variables (lai, canht) are weighted by PFT fraction.  cs is summed over its
pools/layers; t_soil is the deepest layer.  Annual mean = mean of 12 monthly
means (365_day calendar, equal-length enough for a drift check).
usage: python spinup_timeseries.py <output_dir> <run_id> <y0> <y1> [csv]
"""
import os
import sys
import numpy as np
from netCDF4 import Dataset

MASK = '/home/ydkoh/JULES_runs/ancil/global_1deg/jules_perennial_snow_mask_1deg.nc'
snowm = None
if os.path.exists(MASK):
    with Dataset(MASK) as m:
        snowm = m.variables['perennial_snow'][:] == 1

d, rid, y0, y1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
csv = sys.argv[5] if len(sys.argv) > 5 else None
VARS = ['lai', 'canht', 'cv', 'cs', 'gpp_gb', 'npp_gb', 'resp_s_gb', 'latent_heat', 'ftl_gb',
        't1p5m_gb', 'runoff', 'smc_tot', 't_soil', 'snow_mass_gb']
# unit conversions for readability
SCALE = {'gpp_gb': 86400 * 1000, 'npp_gb': 86400 * 1000, 'resp_s_gb': 86400 * 1000,   # kgC/m2/s -> gC/m2/day
         'runoff': 86400}                                                            # kg/m2/s -> mm/day

rows = []
for y in range(y0, y1 + 1):
    with Dataset('%s/%s.monthly.%d.nc' % (d, rid, y)) as f:
        f.set_auto_mask(False)
        lat = np.squeeze(f.variables['latitude'][:])
        npt = lat.size
        frac = np.squeeze(f.variables['frac'][:]).astype('f8')       # (12, ntile, np)
        ice = frac[0, -1] > 0.999                                    # ice is the last tile
        perm = np.zeros(npt, bool)
        if snowm is not None:
            lon = np.squeeze(f.variables['longitude'][:]) % 360
            perm = snowm[np.rint(lat + 89.5).astype(int), np.rint(lon).astype(int) % 360] & ~ice
        w = np.cos(np.deg2rad(lat)) * ~ice * ~perm
        out = {}
        if perm.any():
            out['snow_max_mask'] = np.squeeze(f.variables['snow_mass_gb'][:]).astype('f8').mean(0)[perm].max()
        for v in VARS:
            a = np.squeeze(f.variables[v][:]).astype('f8')           # (12, ..., np)
            if v in ('lai', 'canht'):
                fp = frac[:, :a.shape[1]]
                a = np.nansum(a * fp, axis=1) / np.maximum(fp.sum(axis=1), 1e-12)
            elif v == 't_soil':
                a = a[:, -1]
            elif a.ndim > 2:
                a = a.reshape(a.shape[0], -1, npt).sum(axis=1)
            a = a.mean(axis=0) * SCALE.get(v, 1.0)                   # annual mean per point
            ok = np.isfinite(a) & (w > 0)
            out[v] = (a[ok] * w[ok]).sum() / w[ok].sum()
        rows.append((y, out))

hdr = 'year ' + ' '.join('%10s' % v[:10] for v in VARS)
print('%s  (non-ice land %d pts; gpp/npp/resp_s gC/m2/d, runoff mm/d, cv/cs kgC/m2, smc_tot kg/m2)'
      % (rid, int((~ice).sum())))
print(hdr)
for y, o in rows:
    print('%d ' % y + ' '.join('%10.4g' % o[v] for v in VARS))
if len(rows) >= 6:
    yrs = np.array([r[0] for r in rows[-5:]], 'f8')
    print('last-5-yr slope /yr: ' + ', '.join('%s %+.3g' % (v, np.polyfit(yrs, [r[1][v] for r in rows[-5:]], 1)[0])
                                              for v in VARS))
if csv:
    cols = VARS + (['snow_max_mask'] if 'snow_max_mask' in rows[0][1] else [])
    with open(csv, 'w') as fo:
        fo.write('year,' + ','.join(cols) + '\n')
        for y, o in rows:
            fo.write('%d,' % y + ','.join('%.6g' % o[v] for v in cols) + '\n')
