#!/bin/bash
cd ~/JULES_runs/test_gswp3_static
export LD_LIBRARY_PATH=/usr/local/netcdf/4.6.1_gcc85/lib:/usr/local/hdf5/1.10.5/lib:/usr/local/zlib/1.2.11/lib:$LD_LIBRARY_PATH
echo "=== JULES GSWP3 static-veg run ==="
echo "Start: $(grep main_run_start timesteps.nml)"
time ~/jules-vn7.4/build/bin/jules.exe
echo "=== exit=$? $(date) ==="
ls -lh output/ 2>/dev/null
