#!/home/ydkoh/anaconda3/bin/python
"""
Convert ERA5 hourly data to CLM atmospheric forcing format.
Output: single monthly file with all variables combined.
"""

import numpy as np
import xarray as xr
from datetime import datetime, timedelta
import os
import glob

def era5_files(var_name, year, month):
    """Get all daily ERA5 files for given month."""
    from calendar import monthrange
    base = f"/data1/ERA5/single_level/hourly_0.25/{var_name}/dataset"
    days_in_month = monthrange(year, month)[1]
    files = []
    for day in range(1, days_in_month + 1):
        date_str = f"{year}{month:02d}{day:02d}"
        pattern = f"{base}/ERA5h_{date_str}.nc"
        if os.path.exists(pattern):
            files.append(pattern)
    return sorted(files)

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
        files = era5_files(era5_var, year, month)
        if not files:
            print(f"  WARNING: {era5_var} not found for {year}-{month:02d}")
            continue
        print(f"  Loading {era5_var} ({len(files)} files)...")
        ds_list = [xr.open_dataset(f) for f in files]
        ds_merged = xr.concat(ds_list, dim='time')
        var_name = list(ds_merged.data_vars)[0]
        var_data = ds_merged[var_name]

        # Resample precipitation to 6-hourly by summing
        if era5_var in ['total_precipitation', 'snowfall']:
            var_data = var_data.resample(time='6H').sum(dim='time')

        data[clm_var] = var_data
        for ds in ds_list:
            ds.close()

    # Use ERA5 native coordinate names
    ref = data['Tair']
    lat = ref.latitude.values
    lon = ref.longitude.values
    times = ref.time.values

    # Create output dataset with ERA5 dimensions
    out_ds = xr.Dataset(
        coords={
            'time': times,
            'latitude': ('latitude', lat),
            'longitude': ('longitude', lon),
        }
    )

    # Add variables using ERA5 dimensions
    out_ds['Tair'] = data['Tair'].assign_coords(time=times)
    out_ds['Wind'] = (np.sqrt(data['U10m']**2 + data['V10m']**2)).assign_coords(time=times)
    out_ds['Qair'] = calc_specific_humidity(data['Tair'], data['D2m'], data['PSurf']).assign_coords(time=times)
    out_ds['PSurf'] = data['PSurf'].assign_coords(time=times)
    out_ds['LWdown'] = data['LWdown'].assign_coords(time=times)
    out_ds['SWdown'] = data['SWdown'].assign_coords(time=times)
    out_ds['Rainf'] = (data['Precip'] - data['Snowf']).assign_coords(time=times)
    out_ds['Snowf'] = data['Snowf'].assign_coords(time=times)

    # Set attributes
    for var in ['Tair', 'Wind', 'Qair', 'PSurf', 'LWdown', 'SWdown', 'Rainf', 'Snowf']:
        out_ds[var].attrs['_FillValue'] = np.nan
        out_ds[var].attrs['missing_value'] = -32767

    out_ds['latitude'].attrs['units'] = 'degrees_north'
    out_ds['longitude'].attrs['units'] = 'degrees_east'

    # Write output
    output_file = f"{output_dir}/{year}-{month:02d}.nc"
    print(f"  Writing {output_file}...")
    encoding = {var: {'zlib': True, 'complevel': 4} for var in out_ds.data_vars}
    encoding['time'] = {'units': 'hours since 1900-01-01', 'calendar': 'standard'}
    out_ds.to_netcdf(output_file, encoding=encoding)
    print(f"  Done: {output_file} ({os.path.getsize(output_file)/1e9:.1f} GB)")

    return output_file

if __name__ == '__main__':
    # Test: 1979-01
    create_clm_forcing(1979, 1)
