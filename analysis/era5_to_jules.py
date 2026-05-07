#!/usr/bin/env python3
"""
ERA5 to JULES forcing conversion script
Converts ERA5 hourly data to JULES monthly NetCDF format
"""

import numpy as np
import xarray as xr
from pathlib import Path
import calendar
from datetime import datetime, timedelta

# Configuration
ERA5_DATA_DIR = Path("/data1/ERA5/single_level/hourly_0.25")
OUTPUT_DIR = Path("/data2/ydkoh/era5_forcing")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Years to process (test: 1979-1980)
YEAR_START = 1979
YEAR_END = 1980

# JULES variable mapping: (ERA5_var, JULES_var, JULES_var_name, conversion_func)
VARS = [
    ("ssrd", "sw_down", "SWdown", lambda x: x / 3600),  # J/m² -> W/m² (divide by 3600 for hourly)
    ("strd", "lw_down", "LWdown", lambda x: x / 3600),  # J/m² -> W/m²
    ("tp", "precip", "Rainf", lambda x: x / 3600),      # m -> kg/m²/s (assume 1000 kg/m³)
    ("t2m", "t", "Tair", lambda x: x),                  # K -> K (no conversion)
    ("sp", "pstar", "PSurf", lambda x: x),              # Pa -> Pa (no conversion)
]

def get_wind_speed(u10, v10):
    """Calculate wind speed from u and v components"""
    return np.sqrt(u10**2 + v10**2)

def create_monthly_file(year, month, data_dict):
    """Create a monthly JULES forcing file"""

    # Create output filename
    output_file = OUTPUT_DIR / f"{year:04d}-{month:02d}.nc"

    # Combine all variables into a dataset
    ds = xr.Dataset(data_vars=data_dict)

    # Add time coordinate with standard calendar
    ds["time"].attrs["calendar"] = "standard"
    ds["time"].attrs["units"] = "hours since 1979-01-01 00:00:00"
    ds["time"].attrs["long_name"] = "time"

    # Add variable attributes
    ds["sw_down"].attrs = {"units": "W m-2", "long_name": "Surface solar radiation downwards"}
    ds["lw_down"].attrs = {"units": "W m-2", "long_name": "Surface thermal radiation downwards"}
    ds["precip"].attrs = {"units": "kg m-2 s-1", "long_name": "Precipitation"}
    ds["t"].attrs = {"units": "K", "long_name": "Air temperature at 2m"}
    ds["pstar"].attrs = {"units": "Pa", "long_name": "Surface pressure"}
    ds["wind"].attrs = {"units": "m s-1", "long_name": "Wind speed at 10m"}

    # Global attributes
    ds.attrs = {
        "title": f"JULES forcing data from ERA5 ({year:04d}-{month:02d})",
        "source": "ERA5 reanalysis data",
        "Conventions": "CF-1.6"
    }

    # Write to file
    ds.to_netcdf(output_file, unlimited_dims=["time"])
    print(f"Created: {output_file}")

    return output_file

def process_year_month(year, month):
    """Process a single month of ERA5 data"""

    # Load ERA5 data for this month
    data_files = list(ERA5_DATA_DIR.glob(f"{year:04d}{month:02d}*.nc"))

    if not data_files:
        print(f"Warning: No data found for {year:04d}-{month:02d}")
        return None

    print(f"Processing {year:04d}-{month:02d} ({len(data_files)} files)")

    # Load and concatenate all files for this month
    datasets = []
    for file in sorted(data_files):
        try:
            ds = xr.open_dataset(file)
            datasets.append(ds)
        except Exception as e:
            print(f"  Error reading {file}: {e}")
            continue

    if not datasets:
        print(f"  No valid data for {year:04d}-{month:02d}")
        return None

    # Concatenate along time dimension
    era5_data = xr.concat(datasets, dim="time")

    # Extract variables
    data_dict = {}
    time_values = []

    for era5_var, jules_var, jules_name, convert_func in VARS:
        if era5_var not in era5_data.data_vars:
            print(f"  Warning: Variable {era5_var} not found in ERA5 data")
            continue

        # Get variable and apply conversion
        var_data = era5_data[era5_var]
        converted = convert_func(var_data)

        # Average over space if needed and store
        data_dict[jules_var] = converted

    # Handle wind separately (from u10 and v10)
    if "u10m" in era5_data.data_vars and "v10m" in era5_data.data_vars:
        u10 = era5_data["u10m"]
        v10 = era5_data["v10m"]
        wind_speed = get_wind_speed(u10, v10)
        data_dict["wind"] = wind_speed
    else:
        print(f"  Warning: Wind components not found for {year:04d}-{month:02d}")

    # Handle humidity (from specific humidity or dewpoint)
    if "q" in era5_data.data_vars:
        data_dict["q"] = era5_data["q"]
    elif "d2m" in era5_data.data_vars:
        print(f"  Note: Using dewpoint temperature, humidity calculation needed")
        # TODO: Calculate humidity from dewpoint if needed
    else:
        print(f"  Warning: Humidity/dewpoint not found for {year:04d}-{month:02d}")

    # Create output file
    try:
        create_monthly_file(year, month, data_dict)
    except Exception as e:
        print(f"  Error creating output file: {e}")
        return None

    return str(OUTPUT_DIR / f"{year:04d}-{month:02d}.nc")

def main():
    """Main processing loop"""
    print(f"Converting ERA5 data ({YEAR_START}-{YEAR_END}) to JULES forcing format")
    print(f"Output directory: {OUTPUT_DIR}")

    processed_files = []

    for year in range(YEAR_START, YEAR_END + 1):
        for month in range(1, 13):
            output_file = process_year_month(year, month)
            if output_file:
                processed_files.append(output_file)

    print(f"\nSuccessfully created {len(processed_files)} forcing files")
    print(f"Output directory: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
