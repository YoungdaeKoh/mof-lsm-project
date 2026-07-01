#!/usr/bin/env python3
"""
lm4_to_latlon.py — LM4 압축 cubed-sphere land 출력을 규칙 lat-lon NetCDF으로 변환.

배경 (오늘의 시행착오 박제):
  LM4 land 진단 파일(예: 19810101.land_annual.tile{1..6}.nc)은 변수를 **압축
  land-point 차원** `grid_index`(CF 속성 compress="grid_yt grid_xt") 위에 6개
  cubed-sphere 타일로 저장한다. 파일 안의 geolon_t/geolat_t 는 이 run에서 0/fill로
  나와 쓸 수 없었고, **유효한 지리좌표는 커플러 history 파일의 lndExp_lon/lndExp_lat**
  (shape (ntile, ny, nx)) 에 있다. 따라서:
    grid_index → (j,i) 분해(j=idx//nx, i=idx%nx) → lndExp_lon[t,j,i] 로 좌표 복원
    → 각 land point를 규칙 lat-lon 격자에 binning(셀 평균) → ncview/cdo/xarray로 바로 열림.
  scatter로 찍으면 극 타일이 부채살로 퍼지므로 반드시 binning(규칙격자)으로 변환한다.

사용 (서버 anaconda):
  python lm4_to_latlon.py --prefix 19810101.land_annual \
      --rundir /data2/ydkoh/lm4/RUN/lm4_spinup \
      --coords auto --vars LAI --res 1.0 --rec all --out land_annual_latlon.nc
  # --vars all 로 grid_index 위 모든 변수 변환. --coords 에 특정 cpl.hi.lnd 파일 지정 가능.
  # 3D 변수(z 차원)는 --level N (기본 0=표층) 한 층만 변환.

변환 결과 NetCDF: lon(deg_east), lat(deg_north), [time], <var>(... lat, lon).
NaN = land 없음. cdo/ncview/xarray 표준 호환.
"""
import argparse, glob, os
import numpy as np
from netCDF4 import Dataset


def get_coords(rundir, coords):
    f = sorted(glob.glob(f"{rundir}/ufs.cpld.cpl.hi.lnd.*.nc"))[0] if coords == "auto" else coords
    c = Dataset(f)
    LON = np.array(c.variables["lndExp_lon"][0])   # (ntile, ny, nx), valid geographic coords
    LAT = np.array(c.variables["lndExp_lat"][0])
    c.close()
    return LON, LAT, os.path.basename(f)


def main():
    p = argparse.ArgumentParser(description="LM4 compressed land output -> regular lat-lon NetCDF")
    p.add_argument("--prefix", required=True, help="e.g. 19810101.land_annual (without .tileN.nc)")
    p.add_argument("--rundir", default=".")
    p.add_argument("--coords", default="auto", help="'auto' (first cpl.hi.lnd) or a cpl.hi.lnd*.nc path")
    p.add_argument("--vars", default="all", help="comma list of variable names, or 'all'")
    p.add_argument("--res", type=float, default=1.0, help="target grid resolution (deg)")
    p.add_argument("--rec", default="all", help="'all' | 'last' | integer time index")
    p.add_argument("--level", type=int, default=0, help="vertical level for 3D vars (default 0=surface)")
    p.add_argument("--ntile", type=int, default=6)
    p.add_argument("--out", required=True)
    a = p.parse_args()

    LON, LAT, cf = get_coords(a.rundir, a.coords)
    _, ny, nx = LON.shape

    # ---- target regular grid ----
    lon_e = np.arange(-180, 180 + a.res, a.res)
    lat_e = np.arange(-90, 90 + a.res, a.res)
    lon_c = 0.5 * (lon_e[:-1] + lon_e[1:])
    lat_c = 0.5 * (lat_e[:-1] + lat_e[1:])
    nlon, nlat = lon_c.size, lat_c.size

    # ---- discover variables / time on tile 1 ----
    t1 = Dataset(f"{a.rundir}/{a.prefix}.tile1.nc")
    cdim = "grid_index" if "grid_index" in t1.dimensions else "tile_index"
    gridvars = [v for v in t1.variables
                if cdim in t1.variables[v].dimensions and v != cdim]
    varlist = gridvars if a.vars == "all" else a.vars.split(",")
    has_time = "time" in t1.dimensions
    nt = t1.dimensions["time"].size if has_time else 1
    t1.close()
    recs = list(range(nt)) if a.rec == "all" else ([nt - 1] if a.rec == "last" else [int(a.rec)])

    # ---- decompress land-point geographic coords (once) ----
    glon, glat = [], []
    for t in range(1, a.ntile + 1):
        nc = Dataset(f"{a.rundir}/{a.prefix}.tile{t}.nc")
        gi = np.array(nc.variables[cdim][:]).astype(int)
        nc.close()
        j, i = gi // nx, gi % nx
        glon.append(LON[t - 1, j, i]); glat.append(LAT[t - 1, j, i])
    GLON = np.concatenate(glon); GLAT = np.concatenate(glat)
    GLON = np.where(GLON > 180, GLON - 360, GLON)
    ix = np.clip(np.digitize(GLON, lon_e) - 1, 0, nlon - 1)
    iy = np.clip(np.digitize(GLAT, lat_e) - 1, 0, nlat - 1)
    flat = iy * nlon + ix                                 # flat bin index per land point

    def bin_field(d):                                     # land-point vector -> (nlat,nlon) cell mean
        d = np.where(d < 1e30, d, np.nan)
        s = np.bincount(flat, weights=np.nan_to_num(d), minlength=nlon * nlat)
        c = np.bincount(flat, weights=(~np.isnan(d)).astype(float), minlength=nlon * nlat)
        return np.where(c > 0, s / np.maximum(c, 1), np.nan).reshape(nlat, nlon)

    # ---- write output ----
    out = Dataset(a.out, "w", format="NETCDF4")
    out.createDimension("lon", nlon); out.createDimension("lat", nlat)
    out.createVariable("lon", "f4", ("lon",))[:] = lon_c
    out.createVariable("lat", "f4", ("lat",))[:] = lat_c
    out.variables["lon"].units = "degrees_east"; out.variables["lat"].units = "degrees_north"
    multi = len(recs) > 1
    if multi:
        out.createDimension("time", len(recs))
        out.createVariable("time", "f4", ("time",))[:] = recs
    out.history = f"lm4_to_latlon.py: {a.prefix} -> {a.res}deg regular grid; coords={cf}"

    written = []
    for vn in varlist:
        try:
            per = []
            for r in recs:
                cols = []
                for t in range(1, a.ntile + 1):
                    nc = Dataset(f"{a.rundir}/{a.prefix}.tile{t}.nc")
                    v = nc.variables[vn]
                    dims = v.dimensions
                    arr = np.array(v[:], dtype=float)
                    nc.close()
                    # reduce to a 1D land-point vector for record r / level
                    if "time" in dims:
                        arr = arr[r]                       # drop time
                    if arr.ndim == 2:                      # (z, gp) after time-drop
                        arr = arr[a.level]                 # pick level
                    cols.append(arr.ravel())
                per.append(bin_field(np.concatenate(cols)))
            dims = ("time", "lat", "lon") if multi else ("lat", "lon")
            ov = out.createVariable(vn, "f4", dims, fill_value=np.nan, zlib=True)
            ov[:] = np.array(per) if multi else per[0]
            written.append(vn)
        except Exception as e:
            print(f"  skip {vn}: {e}")
    out.close()
    print(f"wrote {a.out}: vars={written}, grid={nlat}x{nlon}@{a.res}deg, recs={len(recs)}, coords={cf}")


if __name__ == "__main__":
    main()
