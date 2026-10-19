#!/bin/bash
# Copy ERA5-Land monthly 0.1 deg (global, 1950-2025, one nc per month) from climate:/data1 to the local archive.
# Only dataset/*.nc (grib duplicates skipped). Same layout as the local ERA5L_SWE_monthly (ERA5m-land_YYYYMM.nc).
SRC=/data1/ERA5/land_level/monthly_0.1
DST=/Volumes/data02/ERA5/ERA5_Land/monthly_0.1
for v in volumetric_soil_water_layer_1 volumetric_soil_water_layer_2 volumetric_soil_water_layer_3 volumetric_soil_water_layer_4 \
         soil_temperature_level_1 soil_temperature_level_2 soil_temperature_level_3 soil_temperature_level_4 \
         surface_latent_heat_flux surface_sensible_heat_flux skin_temperature; do
  mkdir -p $DST/$v
  rsync -a --include='ERA5m-land_*.nc' --exclude='*' climate:$SRC/$v/dataset/ $DST/$v/ || echo "FAIL $v"
  echo "$v: $(ls $DST/$v | wc -l) files $(date +%H:%M)"
done
echo ALLDONE
