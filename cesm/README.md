# CESM2.1.5 / CLM5 Setup and Execution

## CRITICAL: Module Loading (Mandatory)

**Before any CESM2 work on climate00, ALWAYS source:**
```bash
source /home/ydkoh/CESM2.module.sh
```

This is now added to climate00's global `~/.cshrc`, so it loads automatically on login. But if working in a new shell or non-interactive session, source explicitly.

**Loaded modules:**
- intel21/compiler-21
- intel21/intelmpi-21
- intel21/netcdf-4.6.1
- intel21/hdf5-1.10.5

**Verify after loading:**
```bash
echo $NETCDF   # Should show /usr/local/netcdf/4.6.1_intel21
nc-config --version
nf-config --version
```

## Test Case: clm5_test01

**Setup script:** `/home/ydkoh/run_scripts/test.csh`

Run workflow:
```bash
ssh climate
source /home/ydkoh/CESM2.module.sh   # If not auto-loaded
bash /home/ydkoh/run_scripts/test.csh  # Creates case, builds
cd ~/CESM/cases/clm5_test01
./.case.run                             # Execute
```

**Output location:** `/data2/ydkoh/cesm2_output/clm5_test01/`

## Configuration Details

See `cases/clm5_2010_era5_setup.md` for detailed case setup instructions.

## ERA5 Forcing Data

Location: `/data1/ERA5/single_level/monthly_1.0/`
- Monthly resolution, 1.0° grid
- Variables: 2m_dewpoint_temperature, etc.
- Years: 2007 onwards

## Known Issues

### 1. F2000climo_test1 Input Files (Blocking)
- **Problem**: Cannot download/write to `/data1/CESM2_INPUT/` due to permission restrictions
  - Parent directory has 777 perms but owned by `minseok7kim`
  - SVN download fails: `PermissionError: [Errno 13] Permission denied: '/data1/CESM2_INPUT/atm/waccm'`
- **Solution**: Contact minseok7kim to grant write access or pre-create required subdirectories:
  - `/data1/CESM2_INPUT/atm/waccm/lb/`, `/data1/CESM2_INPUT/cpl/gridmaps/`, etc. (70+ files)
  - Alternatively, run simpler test cases (clm5_test02 is land-only)

### 2. climate00 Shell Startup Noise (Development Blocker)
- **Problem**: ~/.cshrc outputs huge module list on non-interactive SSH, breaking SCP and piped commands
  - `scp` fails with "Received message too long 796226418"
  - Bash heredocs fail with "EOF: Command not found"
  - Piped SSH commands fail with "Ambiguous output redirect"
- **Workaround**: Run commands directly on climate00 via interactive SSH session

### 3. clm5_test02 (Verified Working)
- Land-only case with ERA5 forcing (2010-2019)
- Multi-node distribution: climate01:48, climate02:48 (via mvapich2.hosts)
- Status: Built successfully, ready to run
- **To run**: `ssh climate; cd ~/CESM/cases/clm5_test02; ./.case.run`
