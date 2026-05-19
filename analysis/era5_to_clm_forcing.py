#!/usr/bin/env python3
"""
Convert ERA5 hourly data to CLM atmospheric forcing format.
Output: single monthly file with all variables combined.
"""

import numpy as np
import xarray as xr
from datetime import datetime, timedelta
import os
import glob

def era5_path(var_name, year, month):
    """Build ERA5 path for variable."""
    base = f"/data1/ERA5/single_level/hourly_0.25/{var_name}"
    pattern = f"{base}/*{year}{month:02d}*.nc"
    files = glob.glob(pattern)
    return files[0] if files else None

def calc_specific_humidity(t2m, d2m, mslp):
    """
    Calculate specific humidity from T, Td, pressure.
    T: 2m temperature (K)
    Td: 2m dew point (K)
    P: mean sea level pressure (Pa)
    Returns: specific humidity (kg/kg)
    """
    # Saturation vapor pressure (Magnus formula)
    es = 611.2 * np.exp(17.62 * (d2m - 273.15) / (d2m - 29.65))
    # Actual vapor pressure
    e = es
    # Specific humidity
    q = 0.622 * e / (mslp - 0.378 * e)
    return q.clip(0, 0.05)  # Clamp to realistic range

def create_clm_forcing(year, month, output_dir="/data2/ydkoh/era5_clm_forcing"):
    """Create single CLM forcing file for given month."""
    os.makedirs(output_dir, exist_ok=True)

    print(f"Processing {year}-{month:02d}...")

    # Load ERA5 variables
    vars_mapping = {
        '2m_temperature': 'Tair',
        '10m_u_component_of_wind': 'U10m',
        '10m_v_component_of_wind': 'V10m',
        '2m_dewpoint_temperature': 'D2m',
        'mean_sea_level_pressure': 'PSurf',
        'surface_solar_radiation_downwards': 'SWdown',
        'mean_surface_downward_long_wave_radiation_flux': 'LWdown',
        'total_precipitation': 'Precip',
        'snowfall': 'Snowf',
    }

    data = {}
    for era5_var, clm_var in vars_mapping.items():
        path = era5_path(era5_var, year, month)
        if path is None:
            print(f"  WARNING: {era5_var} not found for {year}-{month:02d}")
            continue
        print(f"  Loading {era5_var}...")
        ds = xr.open_dataset(path)
        var_name = list(ds.data_vars)[0]
        data[clm_var] = ds[var_name]
        ds.close()

    # Align time coordinates
    times = data['Tair'].time.values
    nt = len(times)
    nlat = len(data['Tair'].latitude)
    nlon = len(data['Tair'].longitude)

    # Initialize output with Tair structure
    ref = data['Tair']
    lat = ref.latitude.values
    lon = ref.longitude.values

    # Create output dataset
    out_ds = xr.Dataset(
        coords={
            'time': times,
            'lat': ('lat', lat),
            'lon': ('lon', lon),
        }
    )

    # Add variables with consistent naming
    out_ds['Tair'] = data['Tair']
    out_ds['Wind'] = np.sqrt(data['U10m']**2 + data['V10m']**2)
    out_ds['Qair'] = calc_specific_humidity(data['Tair'], data['D2m'], data['PSurf'])
    out_ds['PSurf'] = data['PSurf']
    out_ds['LWdown'] = data['LWdown']
    out_ds['SWdown'] = data['SWdown']
    out_ds['Rainf'] = data['Precip'] - data['Snowf']  # Rain = total - snow
    out_ds['Snowf'] = data['Snowf']

    # Set attributes
    for var in ['Tair', 'Wind', 'Qair', 'PSurf', 'LWdown', 'SWdown', 'Rainf', 'Snowf']:
        out_ds[var].attrs['_FillValue'] = np.nan
        out_ds[var].attrs['missing_value'] = -32767

    out_ds['time'].attrs['units'] = 'hours since 1900-01-01'
    out_ds['time'].attrs['calendar'] = 'standard'
    out_ds['lat'].attrs['units'] = 'degrees_north'
    out_ds['lon'].attrs['units'] = 'degrees_east'

    # Write output
    output_file = f"{output_dir}/{year}-{month:02d}.nc"
    print(f"  Writing {output_file}...")
    out_ds.to_netcdf(output_file, encoding={var: {'zlib': True, 'complevel': 4} for var in out_ds.data_vars})
    print(f"  Done: {output_file} ({os.path.getsize(output_file)/1e9:.1f} GB)")

    return output_file

if __name__ == '__main__':
    # Test: 1979-01
    create_clm_forcing(1979, 1)
