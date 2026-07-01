#!/usr/bin/env python3
"""
Convert WFDE5 v3.0 (6h-averaged) to CLM5 forcing format.

WFDE5 differs from the Chanhyuk-ERA5 pipeline in two ways handled here:
  1. One file PER variable per month (not a single combined monthly file).
     Path: /data2/ydkoh/WFDE5_6h/{Var}/{Var}_WFDE5_CRU_YYYYMM_v3.0_6h.nc
  2. lon is -179.75..179.75; CLM/GSWP3 expect 0..360, so we roll+sort.
  3. Precip is split into Rainf + Snowf (both kg m-2 s-1 == mm/s);
     CLM5 PRECTmms = Rainf + Snowf.

Output: one combined monthly file with CLM5 variable names, matching
the era5_to_clm5.py convention (TBOT, QBOT, PBOT, FSDS, FLDS, PRECTmms, WIND).

Usage:  python3 wfde5_to_clm5.py [YEAR_START] [YEAR_END]
        (defaults below if omitted)
"""

import sys
import numpy as np
import xarray as xr
from pathlib import Path

# ---------------------------------------------------------------- config
WFDE5_DIR = Path("/data2/ydkoh/WFDE5_6h")
OUTPUT_DIR = Path("/data2/ydkoh/clm5_forcing_wfde5")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

YEAR_START = int(sys.argv[1]) if len(sys.argv) > 1 else 1979
YEAR_END   = int(sys.argv[2]) if len(sys.argv) > 2 else 2024

# WFDE5 short var (== subdir == internal var name) -> CLM5 name + attrs.
# Rainf/Snowf are handled separately to form PRECTmms.
VARMAP = {
    'Tair':   ('TBOT', 'Temperature at reference height', 'K'),
    'Qair':   ('QBOT', 'Specific humidity at reference height', 'kg/kg'),
    'PSurf':  ('PBOT', 'Atmospheric pressure', 'Pa'),
    'SWdown': ('FSDS', 'Incident solar radiation', 'W/m2'),
    'LWdown': ('FLDS', 'Incident longwave radiation', 'W/m2'),
    'Wind':   ('WIND', 'Wind speed', 'm/s'),
}

FILL = np.float32(1.0e20)


def wfde5_path(var, year, month):
    return WFDE5_DIR / var / f"{var}_WFDE5_CRU_{year:04d}{month:02d}_v3.0_6h.nc"


def load_var(var, year, month):
    """Open a WFDE5 monthly file and return its 3D (time,lat,lon) DataArray."""
    fp = wfde5_path(var, year, month)
    if not fp.exists():
        raise FileNotFoundError(fp)
    ds = xr.open_dataset(fp)
    # pick the data variable with time/lat/lon dims (robust to internal naming)
    da = None
    for name, v in ds.data_vars.items():
        if set(('time', 'lat', 'lon')).issubset(v.dims):
            da = v
            break
    if da is None:
        raise ValueError(f"no (time,lat,lon) variable in {fp}")
    return da


def sort_lon_0360(ds):
    """Roll lon from -180..180 to 0..360 and sort ascending."""
    ds = ds.assign_coords(lon=(ds['lon'] % 360.0))
    ds = ds.sortby('lon')
    return ds


def process_month(year, month):
    print(f"Processing {year:04d}-{month:02d}...")
    try:
        ds_out = xr.Dataset()
        ref = None  # keep a reference grid/time

        # straight-mapped variables
        for var, (clm, long_name, units) in VARMAP.items():
            da = load_var(var, year, month)
            if ref is None:
                ref = da
            ds_out[clm] = (('time', 'lat', 'lon'), da.values)
            ds_out[clm].attrs['long_name'] = long_name
            ds_out[clm].attrs['units'] = units
            ds_out[clm].attrs['_FillValue'] = FILL

        # precip = Rainf + Snowf  (both kg m-2 s-1 == mm/s)
        rain = load_var('Rainf', year, month)
        snow = load_var('Snowf', year, month)
        prect = rain.values + snow.values
        ds_out['PRECTmms'] = (('time', 'lat', 'lon'), prect)
        ds_out['PRECTmms'].attrs['long_name'] = 'Precipitation rate (rain+snow)'
        ds_out['PRECTmms'].attrs['units'] = 'mm/s'
        ds_out['PRECTmms'].attrs['_FillValue'] = FILL

        # coordinates from reference variable
        ds_out = ds_out.assign_coords(
            time=ref['time'], lat=ref['lat'], lon=ref['lon'])

        # lon -180..180 -> 0..360
        ds_out = sort_lon_0360(ds_out)

        # global attributes
        ds_out.attrs['title'] = 'CLM5 forcing from WFDE5 v3.0 (CRU)'
        ds_out.attrs['source'] = f'WFDE5 v3.0 6h-mean {year:04d}-{month:02d}'
        ds_out.attrs['note'] = 'lon rolled to 0-360; PRECTmms = Rainf+Snowf'

        out = OUTPUT_DIR / f"{year:04d}-{month:02d}_clm5.nc"
        ds_out.to_netcdf(out, unlimited_dims=['time'])
        print(f"  Created: {out}")
        return str(out)

    except FileNotFoundError as e:
        print(f"  Skip (missing): {e}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print(f"WFDE5 -> CLM5  ({YEAR_START}-{YEAR_END})  out: {OUTPUT_DIR}")
    n = 0
    for year in range(YEAR_START, YEAR_END + 1):
        for month in range(1, 13):
            if process_month(year, month):
                n += 1
    print(f"\nCreated {n} CLM5 forcing files")


if __name__ == '__main__':
    main()
