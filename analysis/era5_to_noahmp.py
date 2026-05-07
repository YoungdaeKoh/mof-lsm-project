#!/usr/bin/env python3
"""
Chanhyuk's ERA5 to Noah-MP/HRLDAS forcing conversion script.
Converts 6-hourly 0.5° global ERA5 to hourly regional WRF-format NetCDF.
"""

import numpy as np
import xarray as xr
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Configuration
ERA5_DATA_DIR = Path("/home/ydkoh/MOF_LSM_project/data/era5_input")
OUTPUT_DIR = Path("/home/ydkoh/MOF_LSM_project/data/noahmp_forcing")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Years to process
YEAR_START = 2010
YEAR_END = 2019

# Domain extraction (East Asia coastal region for testing)
# Lat/Lon in the ERA5 files: lat [-90, 90], lon [-180, 180]
LAT_MIN, LAT_MAX = 20.0, 45.0    # East Asia: ~20-45°N
LON_MIN, LON_MAX = 110.0, 150.0  # East Asia: ~110-150°E

def select_domain(ds, lat_min, lat_max, lon_min, lon_max):
    """Extract a regional domain from global ERA5 data."""
    return ds.sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))

def decompose_wind(wind_speed, month):
    """
    Decompose scalar wind speed into U and V components.
    Uses East Asia climatological wind direction (seasonal).

    Wind direction (meteorological: from which direction):
    - Winter (Dec-Feb): NW (315°)
    - Spring (Mar-May): SE transition
    - Summer (Jun-Aug): SE (135°)
    - Fall (Sep-Nov): NE transition
    """
    # Monthly wind directions (meteorological convention: where wind comes FROM)
    # Convert to math convention: where wind GOES TO
    wind_directions_met = {
        1: 315, 2: 315, 3: 45,   # Dec-Mar: NW->transition->SE
        4: 135, 5: 135, 6: 135,  # Apr-Jun: SE
        7: 135, 8: 135, 9: 45,   # Jul-Sep: SE->transition
        10: 315, 11: 315, 12: 315 # Oct-Dec: NW
    }

    # Get direction for this month (meteorological)
    wind_dir_met = wind_directions_met.get(month, 0)
    # Convert to math convention (add 180°)
    wind_dir_math = (wind_dir_met + 180) % 360
    # Convert to radians
    direction_rad = np.radians(wind_dir_math)

    u_wind = wind_speed * np.cos(direction_rad)
    v_wind = wind_speed * np.sin(direction_rad)

    return u_wind, v_wind

def interpolate_6h_to_hourly(ds):
    """
    Interpolate 6-hourly data to hourly using linear interpolation.
    Handles the time dimension expansion.
    """
    # Get original time coordinates
    time_orig = ds['time'].values

    # Create hourly time array
    time_hourly = []
    for i in range(len(time_orig) - 1):
        t_start = time_orig[i]
        t_end = time_orig[i + 1]
        # Generate 6 intermediate hours between 6-hourly timestamps
        hours = np.linspace(t_start, t_end, 7)[:-1]  # Exclude end to avoid duplication
        time_hourly.extend(hours)
    # Add last 6-hourly timestamp
    time_hourly.append(time_orig[-1])
    time_hourly = np.array(time_hourly)

    # Interpolate each variable
    ds_hourly = ds.copy()
    for var in ds.data_vars:
        if 'time' in ds[var].dims:
            ds_hourly[var] = ds[var].interp(time=time_hourly, method='linear')

    ds_hourly['time'] = time_hourly
    return ds_hourly

def create_wrf_format_file(year, month, ds_hourly, output_path):
    """
    Create WRF-formatted NetCDF file for Noah-MP/HRLDAS.
    Requires dimension names: west_east, south_north, Time
    """
    # Rename dimensions to WRF convention
    ds_out = ds_hourly.copy()

    # Rename lat/lon to south_north/west_east
    ds_out = ds_out.rename({'lat': 'south_north', 'lon': 'west_east'})

    # Rename/create time dimension
    if 'time' in ds_out.dims:
        ds_out = ds_out.rename({'time': 'Time'})

    # Ensure time is unlimited
    ds_out = ds_out.set_coords('Time')

    # Create/add required global attributes for WRF
    ds_out.attrs.update({
        'TITLE': f'Noah-MP forcing from ERA5 ({year:04d}-{month:02d})',
        'SIMULATION_START_DATE': f'{year:04d}-{month:02d}-01_00:00:00',
        'MAP_PROJ': 1,  # Mercator (simplified; could be Lambert Conformal)
        'MMINLU': 'MODIFIED_IGBP_MODIS_NOAH',
        'CEN_LAT': 30.0,
        'CEN_LON': 130.0,
        'TRUELAT1': 30.0,
        'TRUELAT2': 45.0,
        'STAND_LON': 130.0,
        'DX': 10000.0,  # meters (for ~0.1° at equator)
        'DY': 10000.0,
    })

    # Add variable attributes
    if 'T2D' in ds_out.data_vars:
        ds_out['T2D'].attrs = {'units': 'K', 'description': 'Temperature at 2 m'}
    if 'Q2D' in ds_out.data_vars:
        ds_out['Q2D'].attrs = {'units': 'kg/kg', 'description': 'Specific humidity at 2 m'}
    if 'U2D' in ds_out.data_vars:
        ds_out['U2D'].attrs = {'units': 'm/s', 'description': 'U wind at 10 m'}
    if 'V2D' in ds_out.data_vars:
        ds_out['V2D'].attrs = {'units': 'm/s', 'description': 'V wind at 10 m'}
    if 'PSFC' in ds_out.data_vars:
        ds_out['PSFC'].attrs = {'units': 'Pa', 'description': 'Surface pressure'}
    if 'SWDOWN' in ds_out.data_vars:
        ds_out['SWDOWN'].attrs = {'units': 'W/m2', 'description': 'Shortwave radiation'}
    if 'LWDOWN' in ds_out.data_vars:
        ds_out['LWDOWN'].attrs = {'units': 'W/m2', 'description': 'Longwave radiation'}
    if 'RAINRATE' in ds_out.data_vars:
        ds_out['RAINRATE'].attrs = {'units': 'kg/m2/s', 'description': 'Precipitation rate'}

    # Write to file with unlimited time dimension
    ds_out.to_netcdf(output_path, unlimited_dims=['Time'], engine='netcdf4')
    print(f'Created: {output_path}')

def process_month(year, month):
    """Process one month of ERA5 data to Noah-MP format."""
    input_file = ERA5_DATA_DIR / f'{year:04d}-{month:02d}.nc'

    if not input_file.exists():
        print(f'Warning: {input_file} not found')
        return None

    print(f'Processing {year:04d}-{month:02d}...')

    try:
        # Load ERA5 data
        ds = xr.open_dataset(input_file)

        # Extract domain
        ds = select_domain(ds, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX)

        # Rename variables to Noah-MP standard names
        rename_dict = {
            'Tair': 'T2D',
            'Qair': 'Q2D',
            'PSurf': 'PSFC',
            'SWdown': 'SWDOWN',
            'LWdown': 'LWDOWN',
            'Rainf': 'RAINRATE',
        }
        ds = ds.rename({k: v for k, v in rename_dict.items() if k in ds.data_vars})

        # Decompose wind speed into U and V using climatological direction
        if 'Wind' in ds.data_vars:
            wind_speed = ds['Wind']
            u_wind, v_wind = decompose_wind(wind_speed, month)
            ds['U2D'] = (wind_speed.dims, u_wind)
            ds['V2D'] = (wind_speed.dims, v_wind)
            ds = ds.drop_vars('Wind')
        else:
            print(f'  Warning: Wind variable not found')

        # Interpolate 6-hourly to hourly
        print(f'  Interpolating 6-hourly to hourly...')
        ds = interpolate_6h_to_hourly(ds)

        # Create output file
        output_file = OUTPUT_DIR / f'{year:04d}-{month:02d}_noahmp.nc'
        create_wrf_format_file(year, month, ds, output_file)

        ds.close()
        return str(output_file)

    except Exception as e:
        print(f'  Error: {e}')
        import traceback
        traceback.print_exc()
        return None

def main():
    print(f'Converting ERA5 ({YEAR_START}-{YEAR_END}) to Noah-MP forcing')
    print(f'Output directory: {OUTPUT_DIR}')

    processed_files = []

    for year in range(YEAR_START, YEAR_END + 1):
        for month in range(1, 13):
            output_file = process_month(year, month)
            if output_file:
                processed_files.append(output_file)

    print(f'\nSuccessfully created {len(processed_files)} forcing files')

if __name__ == '__main__':
    main()
