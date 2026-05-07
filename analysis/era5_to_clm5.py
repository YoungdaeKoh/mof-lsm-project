#!/usr/bin/env python3
"""
Convert Chanhyuk ERA5 to CLM5 forcing format.
CLM5 expects specific variable names and dimensions.
"""

import numpy as np
import xarray as xr
from pathlib import Path
from datetime import datetime, timedelta

# Configuration
ERA5_DATA_DIR = Path("/data1/backup/ChanhyukChoi/002.JULES_RUN/INPUT_DATA/monitoring/92.GPCPobs_ERA5obs")
OUTPUT_DIR = Path("/data2/ydkoh/clm5_forcing")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Years to process
YEAR_START = 2010
YEAR_END = 2019

# CLM5 variable mapping: Chanhyuk ERA5 -> CLM5
VARIABLE_MAP = {
    'Tair': 'TBOT',      # Temperature at reference height (K)
    'Qair': 'QBOT',      # Specific humidity at reference height (kg/kg)
    'PSurf': 'PBOT',     # Atmospheric pressure at surface (Pa)
    'SWdown': 'FSDS',    # Incident solar radiation (W/m2)
    'LWdown': 'FLDS',    # Incident longwave radiation (W/m2)
    'Rainf': 'PRECTmms', # Precipitation rate (mm/s -> needs conversion to mm/s for CLM)
    'Wind': 'WIND'       # Wind speed (m/s)
}

def process_month(year, month):
    """Process one month of ERA5 data to CLM5 format."""
    input_file = ERA5_DATA_DIR / f'{year:04d}-{month:02d}.nc'
    
    if not input_file.exists():
        print(f'Warning: {input_file} not found')
        return None
    
    print(f'Processing {year:04d}-{month:02d}...')
    
    try:
        # Load ERA5 data
        ds = xr.open_dataset(input_file)
        
        # Create output dataset with CLM5 variable names
        ds_out = xr.Dataset()
        
        # Copy coordinates
        ds_out['lat'] = ds['lat']
        ds_out['lon'] = ds['lon']
        ds_out['time'] = ds['time']
        
        # Map variables
        for era5_var, clm5_var in VARIABLE_MAP.items():
            if era5_var in ds.data_vars:
                ds_out[clm5_var] = ds[era5_var]
                
                # Add CLM5 attributes
                if clm5_var == 'TBOT':
                    ds_out[clm5_var].attrs['long_name'] = 'Temperature at reference height'
                    ds_out[clm5_var].attrs['units'] = 'K'
                elif clm5_var == 'QBOT':
                    ds_out[clm5_var].attrs['long_name'] = 'Specific humidity at reference height'
                    ds_out[clm5_var].attrs['units'] = 'kg/kg'
                elif clm5_var == 'PBOT':
                    ds_out[clm5_var].attrs['long_name'] = 'Atmospheric pressure'
                    ds_out[clm5_var].attrs['units'] = 'Pa'
                elif clm5_var == 'FSDS':
                    ds_out[clm5_var].attrs['long_name'] = 'Incident solar radiation'
                    ds_out[clm5_var].attrs['units'] = 'W/m2'
                elif clm5_var == 'FLDS':
                    ds_out[clm5_var].attrs['long_name'] = 'Incident longwave radiation'
                    ds_out[clm5_var].attrs['units'] = 'W/m2'
                elif clm5_var == 'PRECTmms':
                    ds_out[clm5_var].attrs['long_name'] = 'Precipitation rate'
                    ds_out[clm5_var].attrs['units'] = 'mm/s'
                elif clm5_var == 'WIND':
                    ds_out[clm5_var].attrs['long_name'] = 'Wind speed'
                    ds_out[clm5_var].attrs['units'] = 'm/s'
        
        # Add global attributes
        ds_out.attrs['title'] = 'CLM5 forcing from ERA5'
        ds_out.attrs['source'] = f'Chanhyuk ERA5 {year:04d}-{month:02d}'
        
        # Write output file
        output_file = OUTPUT_DIR / f'{year:04d}-{month:02d}_clm5.nc'
        ds_out.to_netcdf(output_file, unlimited_dims=['time'])
        print(f'  Created: {output_file}')
        
        ds.close()
        return str(output_file)
        
    except Exception as e:
        print(f'  Error: {e}')
        import traceback
        traceback.print_exc()
        return None

def main():
    print(f'Converting ERA5 ({YEAR_START}-{YEAR_END}) to CLM5 forcing')
    print(f'Output directory: {OUTPUT_DIR}')
    
    processed_files = []
    
    for year in range(YEAR_START, YEAR_END + 1):
        for month in range(1, 13):
            output_file = process_month(year, month)
            if output_file:
                processed_files.append(output_file)
    
    print(f'\nSuccessfully created {len(processed_files)} CLM5 forcing files')

if __name__ == '__main__':
    main()
