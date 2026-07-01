#!/bin/bash
#====================================================================
# JULES vn7.4 빌드 — gfortran + netcdf-4.6.1_gcc85 (serial/nompi)
# Intel netcdf(__libm_feature_flag 누락)로 실행 불가 → gfortran 우회
#====================================================================
set -e
export PATH=$HOME/fcm/bin:$PATH

# 컴파일러: gfortran (system gcc 8.5.0)
export JULES_PLATFORM=custom
export JULES_COMPILER=gfortran
export JULES_BUILD=normal
export JULES_MPI=nompi
export JULES_OMP=noomp

# NetCDF: gcc85 빌드
GCCNC=/usr/local/netcdf/4.6.1_gcc85
export JULES_NETCDF=netcdf
export JULES_NETCDF_PATH=$GCCNC
export JULES_NETCDF_INC_PATH=$GCCNC/include
export JULES_NETCDF_LIB_PATH=$GCCNC/lib

# HDF5/zlib/curl 링크 (nf-config --flibs 기반)
export JULES_LDFLAGS_EXTRA="-L/usr/local/hdf5/1.10.5/lib -L/usr/local/zlib/1.2.11/lib -lhdf5_hl -lhdf5 -lz -lcurl"
# gfortran 8.5: 인자 불일치를 error 아닌 warning 으로 (10+ 의 -fallow-argument-mismatch 대응)
export JULES_FFLAGS_EXTRA="-Wno-argument-mismatch"

cd $HOME/jules-vn7.4
echo "=== fcm make (gfortran) 시작 ==="
fcm make --new -j 4 -f etc/fcm-make/make.cfg
echo "=== 빌드 종료 (exit=$?) ==="
echo "--- jules.exe 확인 ---"
ls -la $HOME/jules-vn7.4/build/bin/jules.exe
echo "--- ldd (undefined 있나) ---"
ldd $HOME/jules-vn7.4/build/bin/jules.exe | grep -i "not found" || echo "  (not found 없음 = OK)"
