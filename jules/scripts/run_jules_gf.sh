#!/bin/bash
#====================================================================
# JULES gfortran 실행 — gridded 1개월 smoke run
# 런타임 라이브러리: netcdf-4.6.1_gcc85 + hdf5/1.10.5 + zlib (Intel 안 씀)
#====================================================================
cd ~/JULES_runs/test_gridded_gf

# gfortran 빌드 netcdf 런타임 경로
export LD_LIBRARY_PATH=/usr/local/netcdf/4.6.1_gcc85/lib:/usr/local/hdf5/1.10.5/lib:/usr/local/zlib/1.2.11/lib:$LD_LIBRARY_PATH

echo "=== JULES gridded smoke run ==="
echo "Start: $(grep main_run_start timesteps.nml)"
echo "End:   $(grep main_run_end timesteps.nml)"
echo "ldd check:"; ldd ~/jules-vn7.4/build/bin/jules.exe | grep -i "not found" || echo "  libs OK"
echo "=== run 시작 $(date) ==="
time ~/jules-vn7.4/build/bin/jules.exe
echo "=== run 종료 (exit=$?) $(date) ==="
echo "--- output 파일 ---"
ls -lh ~/JULES_runs/test_gridded_gf/output/ 2>/dev/null
