#!/usr/bin/env python3
"""Gate a JULES run's output: all twelve months present, December real, balances closed.

Written because a segment that stops on the month boundary can quietly write
eleven months (LM4 wrote 15 years with 11 months each before anyone noticed),
and because the monthly profile shows zero records until the file is closed.

usage: python chk_jules_year.py <output_dir> <run_id> <year>
exit 0 = pass, 1 = fail (so a chain script can stop on it)
"""
import sys, os
import warnings
import numpy as np
from netCDF4 import Dataset, num2date
warnings.filterwarnings('ignore', category=RuntimeWarning)   # all-NaN slices over ocean

d, run_id, year = sys.argv[1], sys.argv[2], int(sys.argv[3])
f = os.path.join(d, '%s.monthly.%d.nc' % (run_id, year))
fail = []

if not os.path.exists(f):
    print('FAIL: %s missing' % f); sys.exit(1)

with Dataset(f) as m:
    n = m.dimensions['time'].size
    if n != 12:
        fail.append('time records = %d, expected 12' % n)
    if n:
        # JULES stamps a mean at the END of its period (the January mean carries
        # 1 Feb), exactly like CLM5's h0 files, so the bare time axis decodes to
        # [2,3,...,12,1].  time_bounds holds the real period; its midpoint is
        # what identifies the month.  Any analysis that reads `time` straight
        # off is off by one month.
        t = m['time']
        cal = getattr(t, 'calendar', 'standard')
        if 'time_bounds' in m.variables:
            tb = np.array(m['time_bounds'][:])
            mid = tb.mean(axis=1)
        else:
            mid = np.array(t[:])
            fail.append('no time_bounds; month check used the raw (end-stamped) time')
        months = [x.month for x in num2date(mid, t.units, calendar=cal)]
        if months != list(range(1, 13)):
            fail.append('months are %s' % months)

        lat = np.array(m['latitude'][:]).ravel()
        w = np.cos(np.deg2rad(lat))
        fr = np.where(np.array(m['frac'][0]) > 1e19, np.nan, np.array(m['frac'][0]))
        noice = fr[8].ravel() < 0.5

        def lm(a):
            a = np.where(np.asarray(a, dtype='f8') > 1e19, np.nan, np.asarray(a, dtype='f8'))
            k = np.isfinite(a) & noice
            return float((a * w)[k].sum() / w[k].sum())

        # December must hold real numbers, not fill -- the failure mode is a
        # month that exists in the file but was never written to.
        dec = np.array(m['latent_heat'][11]).ravel()
        if not np.isfinite(np.where(dec > 1e19, np.nan, dec)).any():
            fail.append('December latent_heat is all fill')

        r = np.array(m['runoff'][:]); s1 = np.array(m['surf_roff'][:]); s2 = np.array(m['sub_surf_roff'][:])
        for x in (r, s1, s2):
            x[x > 1e19] = np.nan
        wb = float(np.nanmax(np.abs(r - (s1 + s2))))
        if wb > 1e-6:
            fail.append('water balance off by %.2e' % wb)

        fsum = np.nansum(fr, axis=0)
        if abs(np.nanmin(fsum) - 1) > 1e-3 or abs(np.nanmax(fsum) - 1) > 1e-3:
            fail.append('frac tiles sum to %.4f..%.4f' % (np.nanmin(fsum), np.nanmax(fsum)))

        print('%d: 12 months, LH Jan %.2f Jul %.2f Dec %.2f | T1.5m Jan %.2f Jul %.2f | '
              'LAI Jan %.2f Dec %.2f | water bal %.1e'
              % (year, lm(m['latent_heat'][0].ravel()), lm(m['latent_heat'][6].ravel()),
                 lm(m['latent_heat'][11].ravel()), lm(m['t1p5m_gb'][0].ravel()),
                 lm(m['t1p5m_gb'][6].ravel()),
                 lm(np.nanmean(np.where(np.array(m['lai'][0]) > 1e19, np.nan,
                                        np.array(m['lai'][0])), axis=0).ravel()),
                 lm(np.nanmean(np.where(np.array(m['lai'][11]) > 1e19, np.nan,
                                        np.array(m['lai'][11])), axis=0).ravel()),
                 wb))

if fail:
    print('FAIL %d: %s' % (year, '; '.join(fail))); sys.exit(1)
print('PASS %d' % year); sys.exit(0)
