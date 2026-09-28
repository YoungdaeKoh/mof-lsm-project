#!/usr/bin/env python3
"""Build the 1-degree JULES grid_info.nc (and regrid soil/frac) from the 0.5-degree ancillaries.

JULES is standalone: it does not regrid anything.  Every ancillary must sit on
exactly the grid the driving data uses, in the same array order, because JULES
matches by index and not by coordinate -- a longitude convention mismatch would
be silent and would put the Sahara in the Pacific.

The 1-degree GSWP3 forcing (jules_gswp3_1deg, CDO conservative remap) is on
  lon = 0,1,...,359      lat = -89.5,...,89.5
while the 0.5-degree ancillaries are on
  lon = -179.75,...,179.75   lat = -89.75,...,89.75
so the source is rolled to the 0-360 convention before any aggregation.

land_fraction in the 0.5-degree file is already a 0/1 mask (67209 land cells).
JULES treats *any* box with land_fraction > 0 as 100 % land, so aggregating
2x2 with "any land" would inflate the coastline by a full degree.  The default
here is the majority rule (>= 2 of 4 sub-cells); --how any is kept for
comparison.

usage: python make_grid_info_1deg.py [--how majority|any] [--outdir DIR]
"""
import argparse, os
import numpy as np
from netCDF4 import Dataset

SRC_DIR  = '/data1/backup/ChanhyukChoi/002.JULES_RUN/JULES/ancil'
GRID_05  = '/home/ydkoh/JULES_runs/ancil/global/grid_info.nc'
OUT_DEF  = '/home/ydkoh/JULES_runs/ancil/global_1deg'
FILL     = -1.0e20

ap = argparse.ArgumentParser()
ap.add_argument('--how', default='majority', choices=['majority', 'any'])
ap.add_argument('--outdir', default=OUT_DEF)
a = ap.parse_args()
os.makedirs(a.outdir, exist_ok=True)

# ---- target grid: copied from the forcing, not re-derived -------------------
lon1 = np.arange(360, dtype='f8')            # 0 .. 359
lat1 = -89.5 + np.arange(180, dtype='f8')    # -89.5 .. 89.5

ICE_TILE = 8          # jules_surface_types: ice = 9, so index 8 (0-based)

def fix_ice_soil(frac, land):
    """Make every ice cell all-or-nothing, the way the 0.5 deg source is.

    JULES (init_ic.inc) calls a point "ice" as soon as frac(ice) > 0, then
    aborts if that same point is also in the soil list (built from sm_sat > 0),
    and separately errors if the ice fraction is not exactly 1.  A 2x2 mean
    turns the ice margin into mixtures (ice 0.25, vegetation 0.75) that violate
    both rules.  The block decides by majority: ice-dominated blocks become pure
    ice, the rest lose their ice sliver and the remaining eight tiles are
    renormalised to sum to one.  Nothing is invented -- this restores the
    all-or-nothing character the source had.

    Sets the module-level PURE_ICE so the soil file, written next, can zero the
    hydraulic properties at exactly these cells.
    """
    global PURE_ICE
    f = np.array(frac, dtype='f8')
    f[f <= FILL * 0.99] = np.nan
    ice = np.where(np.isfinite(f[ICE_TILE]), f[ICE_TILE], 0.0)

    PURE_ICE = land & (ice >= 0.5)
    mixed    = land & (ice > 0) & (ice < 0.5)

    f[ICE_TILE][mixed] = 0.0                  # drop the sliver
    rest = np.nansum(f[:ICE_TILE], axis=0)
    with np.errstate(invalid='ignore', divide='ignore'):
        scale = np.where(rest > 0, 1.0 / rest, 0.0)
    for k in range(ICE_TILE):
        f[k][mixed] = f[k][mixed] * scale[mixed]

    f[:, PURE_ICE] = 0.0                      # ice-dominated -> pure ice
    f[ICE_TILE][PURE_ICE] = 1.0

    print('  ice: %d pure-ice cells, %d mixed cells cleaned' % (PURE_ICE.sum(), mixed.sum()))
    return np.where(np.isfinite(f), f, FILL)


def roll_to_0360(lon, arr):
    """-180..180 -> 0..360, moving the data with the coordinate (last axis)."""
    k = int(np.sum(lon < 0))
    return np.roll(lon, -k) % 360.0, np.roll(arr, -k, axis=-1)

def agg(field, how):
    """0.5 deg -> 1 deg, 2x2 block mean (nan-aware); returns the block mean."""
    s = field.reshape(180, 2, 360, 2)
    return np.nanmean(s, axis=(1, 3))

with Dataset(GRID_05) as d:
    lon05 = np.array(d['lon'][:])
    lat05 = np.array(d['lat'][:])
    lf05  = np.array(d['land_fraction'][:], dtype='f8')
lon05r, lf05r = roll_to_0360(lon05, lf05)
assert np.all(np.diff(lon05r) > 0), 'rolled longitude is not monotonic'
assert np.all(np.diff(lat05) > 0), 'source latitude is not ascending'

frac_mean = agg(lf05r, a.how)                       # 0, .25, .5, .75, 1
land1 = (frac_mean >= 0.5) if a.how == 'majority' else (frac_mean > 0)
land1 = land1.astype('f4')

LON, LAT = np.meshgrid(lon1, lat1)

out = os.path.join(a.outdir, 'grid_info_1deg.nc')
if os.path.exists(out):
    os.remove(out)
with Dataset(out, 'w', format='NETCDF3_CLASSIC') as o:
    o.createDimension('lon', 360)
    o.createDimension('lat', 180)
    v = o.createVariable('lon', 'f8', ('lon',)); v.units = 'degrees'; v[:] = lon1
    v = o.createVariable('lat', 'f8', ('lat',)); v.units = 'degrees'; v[:] = lat1
    for name, data, ln in (('latitude',  LAT,   'Latitude of grid box centre'),
                           ('longitude', LON,   'Longitude of grid box centre'),
                           ('land_fraction', land1, 'Land fraction of grid box')):
        v = o.createVariable(name, 'f4', ('lat', 'lon'))
        v.units = 'degrees' if name != 'land_fraction' else '-'
        v.missing_value = np.float32(FILL)
        v.long_name = ln
        v[:] = data
    o.source = ('1 deg grid_info built from %s by jules/scripts/make_grid_info_1deg.py'
                % os.path.basename(GRID_05))
    o.grid = 'lon 0..359, lat -89.5..89.5 -- matches jules_gswp3_1deg forcing'
    o.land_mask_rule = ('%s of the four 0.5 deg sub-cells; JULES treats any box with '
                        'land_fraction > 0 as fully land' % a.how)

print('wrote', out)
print('  land cells 1deg: %d (%.1f%% of globe)' % (land1.sum(), 100 * land1.mean()))
print('  0.5deg land cells: %d -> expected ~%d at 1deg' % (lf05.sum(), lf05.sum() / 4))
print('  block-mean histogram:', {float(k): int(v) for k, v in
                                  zip(*np.unique(frac_mean, return_counts=True))})

# ---- which 1 deg cells are ice ---------------------------------------------
# Decided from frac before anything else, because the soil file has to agree:
# JULES builds its soil list from sm_sat > 0 (init_ic.inc), so an ice point must
# carry sm_sat = 0 or it lands in both lists and the run aborts.  The 0.5 deg
# source already follows this convention (at its ice points b/sathh/satcon/
# sm_sat/sm_crit/sm_wilt = 0 and hcap/hcon/albsoil are the ice values).
PURE_ICE = np.zeros_like(land1, dtype=bool)   # filled in by fix_ice_soil (frac is processed first)

# values the 0.5 deg file carries at an ice point
ICE_SOIL_VALUES = {'field1381': 0.0, 'field342': 0.0, 'field333': 0.0,
                   'field332': 0.0, 'field330': 0.0, 'field329': 0.0,
                   'field335': 6.3e5, 'field336': 0.265, 'field1395': 0.75}

# ---- soil and frac on the same grid ---------------------------------------
for src, outname in (('frac.nc', 'frac_1deg.nc'), ('soil.nc', 'soil_1deg.nc')):
    ip = os.path.join(SRC_DIR, src)
    op = os.path.join(a.outdir, outname)
    if os.path.exists(op):
        os.remove(op)
    with Dataset(ip) as d, Dataset(op, 'w', format='NETCDF3_CLASSIC') as o:
        o.createDimension('lon', 360)
        o.createDimension('lat', 180)
        if 'pseudo' in d.dimensions:
            o.createDimension('pseudo', len(d.dimensions['pseudo']))
            pv = o.createVariable('pseudo', 'i4', ('pseudo',))
            pv.units = '-'
            pv[:] = d['pseudo'][:]
        v = o.createVariable('lon', 'f8', ('lon',)); v.units = 'degrees'; v[:] = lon1
        v = o.createVariable('lat', 'f8', ('lat',)); v.units = 'degrees'; v[:] = lat1
        for name in d.variables:
            if name in ('lon', 'lat', 'pseudo'):
                continue
            sv = d[name]
            arr = np.array(sv[:], dtype='f8')
            mv = getattr(sv, 'missing_value', FILL)
            arr[arr <= mv * 0.99 if mv < 0 else arr == mv] = np.nan
            if arr.ndim == 2:
                _, arr = roll_to_0360(lon05, arr)
                new = agg(arr, a.how)
            else:                                    # (pseudo, lat, lon)
                _, arr = roll_to_0360(lon05, arr)
                new = np.stack([agg(arr[k], a.how) for k in range(arr.shape[0])])
            # keep values only where the 1 deg mask says land
            m = land1 > 0
            new = np.where(np.isfinite(new), new, FILL)
            if new.ndim == 2:
                new[~m] = FILL
            else:
                new[:, ~m] = FILL
            dims = ('lat', 'lon') if new.ndim == 2 else ('pseudo', 'lat', 'lon')
            if src == 'frac.nc':
                new = fix_ice_soil(new, m)
            elif name in ICE_SOIL_VALUES:
                new[PURE_ICE] = ICE_SOIL_VALUES[name]
            ov = o.createVariable(name, 'f4', dims)
            ov.units = getattr(sv, 'units', '-')
            ov.missing_value = np.float32(FILL)
            ov[:] = new
        o.source = '1 deg regrid of %s by jules/scripts/make_grid_info_1deg.py' % src
    print('wrote', op)
