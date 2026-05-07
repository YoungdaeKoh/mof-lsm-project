# CLM5 2010-2019 ERA5 Test Case Setup Guide

## Overview
Create and run a CLM5 test case using 2010-2019 Chanhyuk ERA5 forcing on climate00.

## Base Case
- **Parent case**: I2000Clm50Sp (already built)
- **Resolution**: f09_g17 (1° atmosphere, 0.9° land)
- **Compiler**: ifort (Intel)
- **MPI**: mvapich2 or OpenMPI

## Steps on climate00

### 1. Create new case from existing
```bash
cd ~/CESM/cime/scripts
./create_newcase --case ~/CESM/cases/clm5_2010_2019_era5 \
                --compset I2000Clm50Sp \
                --res f09_g17 \
                --mach cheyenne  # or appropriate machine name
```

### 2. Update CAM/CLM forcing file paths
Edit user_nl_clm in case directory:
```
fsurdat = '/data2/ydkoh/clm5_forcing/%y4-%m2_clm5.nc'
```

### 3. Update run times
Edit env_run.xml:
```
STOP_N = 1        (run for 1 month)
STOP_OPTION = nmonths
RUN_STARTDATE = '2010-01-01'
```

### 4. Build and run
```bash
cd ~/CESM/cases/clm5_2010_2019_era5
./case.setup
./case.build
./case.submit
```

## Forcing file requirements
- Location: /data2/ydkoh/clm5_forcing/
- Format: NetCDF with CLM5 variable names
- Variables: TBOT, QBOT, PBOT, FSDS, FLDS, PRECTmms, WIND
- Time: 6-hourly, 1978-2026

## Expected output
- History files: YYYY-MM.clm2.h0.nc
- Location: ~/CESM/cases/clm5_2010_2019_era5/run/

## Notes
- CLM5 requires proper forcing file format (netcdf4 python library)
- Initial conditions: use default or spinup file from glosea
- Verification: check clm*.log files for errors
