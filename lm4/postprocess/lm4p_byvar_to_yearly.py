#!/usr/bin/env python3
"""LM4p per-variable 1-deg files -> one file per year, all variables.

The regrid step (lm4p_to_latlon.py) writes one file per variable holding the
whole 1979-2023 record.  This reshuffles them into the layout the other two
models use -- lm4p_ctl.YYYY.nc with twelve monthly records and every
diagnostic variable -- so that a diagnostic script can open one file per model
per year and not care which model wrote it.

Time is rewritten as days since YYYY-01-01 on the noleap calendar the model
runs, stamped at mid-month.

usage: python lm4p_byvar_to_yearly.py [Y0 Y1]
"""
import glob, os, sys
import numpy as np
from netCDF4 import Dataset

BYVAR = '/data2/ydkoh/lm4/postproc/lm4p_ctl/byvar'
OUT   = '/data2/ydkoh/lm4/postproc/lm4p_ctl/yearly'
FILL  = 1.0e20
MLEN  = np.array([31,28,31,30,31,30,31,31,30,31,30,31], float)
MMID  = np.concatenate(([0.0], np.cumsum(MLEN)[:-1])) + MLEN / 2.0

y0 = int(sys.argv[1]) if len(sys.argv) > 2 else 1979
y1 = int(sys.argv[2]) if len(sys.argv) > 2 else 2023
os.makedirs(OUT, exist_ok=True)

files = sorted(glob.glob(BYVAR + '/*.1deg.nc'))
srcs  = {}
for f in files:
    with Dataset(f) as d:
        var = [v for v in d.variables
               if v not in ('time', 'lat', 'lon') and 'lat' in d[v].dimensions][0]
        srcs[var] = f
print('variables:', len(srcs))

with Dataset(files[0]) as d:
    lat = d['lat'][:]
    lon = d['lon'][:]
    ny0 = int(os.path.basename(files[0]).split('.')[-3].split('-')[0])

for year in range(y0, y1 + 1):
    k = (year - ny0) * 12                      # the file's records are contiguous months
    out = '%s/lm4p_ctl.%d.nc' % (OUT, year)
    if os.path.exists(out):
        os.remove(out)
    with Dataset(out, 'w', format='NETCDF4') as o:
        o.createDimension('time', 12)
        o.createDimension('lat', lat.size)
        o.createDimension('lon', lon.size)
        t = o.createVariable('time', 'f8', ('time',))
        t.units = 'days since %d-01-01 00:00:00' % year
        t.calendar = 'noleap'
        t.long_name = 'time'
        t[:] = MMID
        la = o.createVariable('lat', 'f8', ('lat',)); la.units = 'degrees_north'; la[:] = lat
        lo = o.createVariable('lon', 'f8', ('lon',)); lo.units = 'degrees_east';  lo[:] = lon
        levdims = set()
        for var in sorted(srcs):
            with Dataset(srcs[var]) as d:
                sv = d[var]
                dims = sv.dimensions
                if len(dims) == 4:             # (time, lev, lat, lon)
                    lev = dims[1]
                    if lev not in levdims:
                        o.createDimension(lev, d.dimensions[lev].size)
                        lv = o.createVariable(lev, 'f8', (lev,))
                        lv[:] = d[lev][:]
                        levdims.add(lev)
                    newdims = ('time', lev, 'lat', 'lon')
                else:
                    newdims = ('time', 'lat', 'lon')
                a = sv[k:k+12]
                v = o.createVariable(var, 'f4', newdims, zlib=True, complevel=4,
                                     fill_value=FILL)
                for at in sv.ncattrs():
                    if at not in ('_FillValue', 'missing_value'):
                        try:    v.setncattr(at, sv.getncattr(at))
                        except Exception: pass
                v[:] = a
        o.title = 'LM4p ctl 1979-2023, C96 regridded to 1 deg lat-lon'
        o.source = 'lm4/postprocess/lm4p_to_latlon.py then lm4p_byvar_to_yearly.py'
        o.caveat = ('regridded for viewing and cross-model plotting; absolute '
                    'and global means belong on the native C96 grid')
    print('%d done (%.1f MB)' % (year, os.path.getsize(out) / 1e6), flush=True)
print('ALL DONE %d-%d' % (y0, y1))
