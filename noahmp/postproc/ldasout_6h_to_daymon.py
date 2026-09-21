#!/usr/bin/env python
"""Noah-MP (HRLDAS) 6-hourly LDASOUT -> daily mean -> monthly mean, one month per call.

Fixes the LDASOUT quirks found on the prod_1979_2023 run (NOAHMP_PORTING_NOTES.md sec.12):
  * no time axis (only char `Times`)           -> real `time` coordinate
  * no XLAT/XLONG in LDASOUT                    -> 1-D lat/lon from the HRLDAS setup file
  * two fill values: ocean -1e33, N/A tile -9999 -> single NaN / _FillValue
  * cdo 1.9.3 mis-reads the 4-D (soil/snow layer) variables -> done in xarray instead
  * accumulated vars (UGDRNOFF SFCRNOFF ACSNOW ACSNOM) -> 6h increments, reported as mm/day

Usage: python ldasout_6h_to_daymon.py YYYY MM [--rundir DIR] [--outdir DIR] [--daily]
Run under the server anaconda base env (xarray 2023.6, netCDF4 1.7.4).
"""
import argparse, glob, os, sys, warnings, datetime as dt
import numpy as np, xarray as xr, netCDF4 as nc
warnings.filterwarnings('ignore', category=RuntimeWarning)   # nanmean of all-NaN (ocean) slices

SETUP = '/home/ydkoh/HRLDAS/forcing_GSWP3_1deg/init/HRLDAS_setup_GSWP3_1deg_d01.nc'
ACC_VARS = ['UGDRNOFF', 'SFCRNOFF', 'ACSNOW', 'ACSNOM']   # accumulated since model start (mm)
FILL_THRESH = -9998.0                                     # catches both -1e33 and -9999
OUT_STEP_H = 6

p = argparse.ArgumentParser()
p.add_argument('year', type=int); p.add_argument('month', type=int)
p.add_argument('--rundir', default=os.path.expanduser('~/HRLDAS/forcing_WFDE5_1deg/prod_1979_2023'))
p.add_argument('--outdir', default=os.path.expanduser('~/HRLDAS/forcing_WFDE5_1deg/prod_1979_2023/postproc'))
p.add_argument('--daily', action='store_true', help='also write the daily-mean file')
a = p.parse_args()
Y, M = a.year, a.month
os.makedirs(a.outdir, exist_ok=True)

files = sorted(glob.glob(f'{a.rundir}/{Y}{M:02d}*.LDASOUT_DOMAIN1'))
if not files: sys.exit(f'no files for {Y}-{M:02d}')
# previous 6h file (last stamp of the previous month) for the accumulated-variable difference
t0 = dt.datetime.strptime(os.path.basename(files[0])[:10], '%Y%m%d%H')
prev = f'{a.rundir}/{(t0 - dt.timedelta(hours=OUT_STEP_H)).strftime("%Y%m%d%H")}.LDASOUT_DOMAIN1'
prev = prev if os.path.exists(prev) else None

# --- lat/lon from setup (verified: 1-deg regular, lat[0]=-89.75 ascending) ---
with nc.Dataset(SETUP) as s:
    xlat, xlon = s.variables['XLAT'][0], s.variables['XLONG'][0]
assert np.allclose(xlat, xlat[:, :1]) and np.allclose(xlon, xlon[:1, :]), 'setup grid is not regular lat/lon'
lat, lon = np.asarray(xlat[:, 0], dtype='f8'), np.asarray(xlon[0, :], dtype='f8')

def times_of(ds):
    return np.array([dt.datetime.strptime(b.tobytes().decode().strip(), '%Y-%m-%d_%H:%M:%S')
                     for b in ds['Times'].values], dtype='datetime64[ns]')

def load(fl):
    # eager load (~31 MB/file): open_mfdataset+dask was >10x slower and silently gave all-NaN means here
    ds = xr.concat([xr.open_dataset(f, decode_times=False).load() for f in fl], dim='Time')
    ds = ds.assign_coords(Time=times_of(ds)).rename({'Time': 'time', 'south_north': 'lat', 'west_east': 'lon'})
    ds = ds.drop_vars('Times').assign_coords(lat=lat, lon=lon)
    # HRLDAS stores layered fields as (time, lat, layer, lon); reorder to (time, layer, lat, lon)
    return ds.transpose('time', ..., 'lat', 'lon')

ds = load(files)
n = ds.sizes['time']
print(f'{Y}-{M:02d}: {n} files  {str(ds.time.values[0])[:13]} .. {str(ds.time.values[-1])[:13]}  prev={os.path.basename(prev) if prev else None}')

# --- split static ints / float fields ---
static = {v: ds[v].isel(time=0).drop_vars('time') for v in ds.data_vars if ds[v].dtype.kind == 'i'}
flds = ds[[v for v in ds.data_vars if ds[v].dtype.kind == 'f']]
flds = flds.map(lambda x: x.where(x > FILL_THRESH), keep_attrs=True)   # -1e33 (ocean) and -9999 (N/A tile) -> NaN

# --- accumulated vars -> 6h increment -> mm/day ---
acc = flds[ACC_VARS]
if prev:
    acc = xr.concat([load([prev])[ACC_VARS].map(lambda x: x.where(x > FILL_THRESH)), acc], dim='time')
inc = acc.diff('time') * (24.0 / OUT_STEP_H)   # mm per 6h -> mm/day
if not prev:                                    # first stamp of the whole run: no increment available
    inc = inc.reindex(time=flds.time)
for v in ACC_VARS:
    flds[v] = inc[v]
    flds[v].attrs = dict(ds[v].attrs, units='mm/day',
                         description=ds[v].attrs.get('description', v) + ' (6h increment converted to mm/day)')

# --- daily mean (UTC calendar day: 03/09/15/21Z -> 4 samples) then monthly mean ---
day = flds.resample(time='1D').mean('time', keep_attrs=True)
ndays = flds.time.resample(time='1D').count().rename('nsamp')
mon = day.mean('time', keep_attrs=True).expand_dims(time=np.array([f'{Y}-{M:02d}-01'], dtype='datetime64[ns]'))
for v, s in static.items():
    day[v] = s; mon[v] = s
for d in (day, mon):
    d.attrs = dict(source='Noah-MP HRLDAS prod_1979_2023 LDASOUT 6h instantaneous', fill_note='ocean -1e33 and N/A tile -9999 both -> NaN',
                   accumulated_vars='UGDRNOFF SFCRNOFF ACSNOW ACSNOM converted to 6h-increment mm/day; accumulators inherited from the 30-yr spin-up restart (up to ~1e6 mm) so float32 quantises 6h increments (~0.1 mm) in high-runoff cells; monthly means are exact (last-first)/ndays, daily values noisy there', script=os.path.basename(__file__))
    d.lat.attrs = dict(units='degrees_north'); d.lon.attrs = dict(units='degrees_east')
enc = {'time': dict(units='hours since 1979-01-01 00:00:00', calendar='standard')}
enc |= {v: dict(zlib=True, complevel=4, _FillValue=-9999.0 if day[v].dtype.kind == 'f' else None) for v in day.data_vars}

fm = f'{a.outdir}/noahmp_prod_mon_{Y}{M:02d}.nc'
mon.to_netcdf(fm, encoding=enc, unlimited_dims=['time'])
if a.daily:
    fd = f'{a.outdir}/noahmp_prod_day_{Y}{M:02d}.nc'
    day.to_netcdf(fd, encoding=enc, unlimited_dims=['time']); print('wrote', fd, f'{os.path.getsize(fd)/1e6:.0f} MB')
print('wrote', fm, f'{os.path.getsize(fm)/1e6:.0f} MB')

# --- self-checks (printed, keep short) ---
w = np.cos(np.deg2rad(lat))[:, None] * np.ones((1, lon.size))
ivg = static['IVGTYP'].values; land = (ivg != 15) & (ivg != 17)
def lm(x):  # cos(lat)-weighted non-ice land mean, NaN-aware
    x = np.asarray(x); m = land & np.isfinite(x); return float((x * w)[m].sum() / w[m].sum())
print('nsamp/day min/max:', int(ndays.min()), int(ndays.max()))
print('NaN count on land, monthly LH:', int((~np.isfinite(mon['LH'].values[0]) & land).sum()))
print(f"monthly land-mean: LH {lm(mon['LH'][0]):.1f}  HFX {lm(mon['HFX'][0]):.1f}  FSA {lm(mon['FSA'][0]):.1f}  TRAD {lm(mon['TRAD'][0]):.2f}  SOIL_T(l1) {lm(mon['SOIL_T'][0,0]):.2f}")
# independent cross-check of one daily mean against the 4 raw files
d15 = f'{Y}{M:02d}15'
raw = [nc.Dataset(f) for f in files if os.path.basename(f).startswith(d15)]
def fl2nan(v):  # netCDF4 auto-masks -1e33; fill it back, then NaN both fills (np.where on a masked array is unreliable)
    x = np.array(v.filled(-1e33), dtype='f8'); x[x <= FILL_THRESH] = np.nan; return x
lh_raw = np.nanmean([fl2nan(r['LH'][0]) for r in raw], axis=0); [r.close() for r in raw]
lh_day = day['LH'].sel(time=f'{Y}-{M:02d}-15').squeeze().values   # sel with an exact date drops the time dim
print(f'daily-mean cross-check {d15}: max|xarray-raw| = {np.nanmax(np.abs(lh_day - lh_raw)):.2e}  (n raw files {len(raw)})')
# accumulated closure: sum(increment*6h/24h) over the month == last - first(prev) accumulator
if prev:
    with nc.Dataset(prev) as r0, nc.Dataset(files[-1]) as r1:
        for v in ['UGDRNOFF', 'ACSNOW']:
            tot = (inc[v].sum('time') / (24.0 / OUT_STEP_H)).values
            ref = fl2nan(r1[v][0]) - fl2nan(r0[v][0])
            amax = np.nanmax(np.abs(fl2nan(r1[v][0])))
            print(f'accum closure {v}: max|sum(inc)-(last-prev)| = {np.nanmax(np.abs(tot - ref)):.2e} mm, land-mean {lm(inc[v].mean("time")):.3f} mm/day, '
                  f'n(inc<0) = {int((inc[v].values < 0).sum())}, |accum| max {amax:.3e} mm -> float32 6h-increment resolution ~{np.spacing(np.float32(amax)):.3g} mm')
else:
    print('accum closure skipped (no previous file: run start)')
